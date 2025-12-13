import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import SelectInput from "ink-select-input";
import Spinner from "ink-spinner";
import {
  getAISuggestions,
  type SuggestionResult,
  type KeybindGroup,
} from "../lib/ai.js";

interface Props {
  notify: (msg: string) => void;
  tryKeybinds: (
    keybinds: { keybind: string; command: string; description: string }[],
    groupName: string
  ) => void;
  prefetchedResult: SuggestionResult | null;
  prefetchProgress: string;
  prefetchLoading: boolean;
}

const CATEGORIES = [
  { label: "All (Pre-fetched)", value: "" },
  { label: "Navigation", value: "navigation" },
  { label: "Pane Management", value: "panes" },
  { label: "Window Management", value: "windows" },
  { label: "Session Management", value: "sessions" },
  { label: "Copy Mode", value: "copy" },
  { label: "Productivity", value: "productivity" },
];

// How many groups to show at once (virtual scroll window)
const VISIBLE_GROUPS = 4;

export function DiscoverScreen({
  notify,
  tryKeybinds,
  prefetchedResult,
  prefetchProgress,
  prefetchLoading,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState("");
  const [result, setResult] = useState<SuggestionResult | null>(null);
  const [selectedGroup, setSelectedGroup] = useState(0);
  const [panel, setPanel] = useState<"categories" | "suggestions">("categories");
  const [category, setCategory] = useState("");

  // Use prefetched result when available
  useEffect(() => {
    if (prefetchedResult && !result) {
      setResult(prefetchedResult);
      setPanel("suggestions");
    }
  }, [prefetchedResult]);

  const fetchSuggestions = async (cat: string) => {
    if (cat === "" && prefetchedResult) {
      setResult(prefetchedResult);
      setPanel("suggestions");
      setSelectedGroup(0);
      notify(`Using pre-fetched suggestions!`);
      return;
    }

    setLoading(true);
    setCategory(cat);
    setProgress("Starting...");
    try {
      const suggestions = await getAISuggestions(cat || undefined, (status) => {
        setProgress(status);
      });
      setResult(suggestions);
      setPanel("suggestions");
      setSelectedGroup(0);
      notify(`Found ${suggestions.groups.length} groups!`);
    } catch (e: any) {
      notify(`Error: ${e.message}`);
    } finally {
      setLoading(false);
      setProgress("");
    }
  };

  // Handle keyboard input
  useInput((input, key) => {
    // Only handle navigation when in suggestions panel
    if (panel === "suggestions" && result && result.groups.length > 0) {
      if (input === "h") {
        setPanel("categories");
        return;
      }

      if (input === "j" || key.downArrow) {
        setSelectedGroup(prev => Math.min(prev + 1, result.groups.length - 1));
        return;
      }

      if (input === "k" || key.upArrow) {
        setSelectedGroup(prev => Math.max(prev - 1, 0));
        return;
      }

      if (input === "t" || key.return) {
        const group = result.groups[selectedGroup];
        if (group && group.keybinds.length > 0) {
          tryKeybinds(group.keybinds, group.name);
        }
        return;
      }
    }

    // Handle category panel inputs
    if (panel === "categories") {
      if (input === "l" && !loading && !prefetchLoading && result) {
        setPanel("suggestions");
        return;
      }

      if (input === "s" && !loading && !prefetchLoading) {
        fetchSuggestions(category);
        return;
      }
    }
  });

  const isLoading = loading || (prefetchLoading && !result);
  const currentProgress = loading ? progress : prefetchProgress;

  // Calculate which groups to show (virtual scroll)
  const getVisibleGroups = () => {
    if (!result) return [];

    const total = result.groups.length;
    if (total <= VISIBLE_GROUPS) {
      return result.groups.map((g, i) => ({ group: g, index: i }));
    }

    // Calculate window start to keep selected item visible
    let start = Math.max(0, selectedGroup - Math.floor(VISIBLE_GROUPS / 2));
    start = Math.min(start, total - VISIBLE_GROUPS);

    return result.groups
      .slice(start, start + VISIBLE_GROUPS)
      .map((g, i) => ({ group: g, index: start + i }));
  };

  const visibleGroups = getVisibleGroups();

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Discover New Keybinds</Text>
      <Text color="gray">AI-powered suggestions based on your config</Text>

      <Box marginTop={1} flexDirection="row">
        {/* Categories Panel */}
        <Box
          flexDirection="column"
          width={25}
          borderStyle="single"
          borderColor={panel === "categories" ? "cyan" : "gray"}
          padding={1}
        >
          <Text bold>Categories</Text>
          <SelectInput
            items={CATEGORIES}
            onSelect={(item) => fetchSuggestions(item.value)}
            isFocused={panel === "categories" && !isLoading}
          />
          <Box marginTop={1}>
            <Text color="gray">(s) Search Online</Text>
          </Box>
        </Box>

        {/* Suggestions Panel */}
        <Box
          flexDirection="column"
          flexGrow={1}
          marginLeft={1}
          borderStyle="single"
          borderColor={panel === "suggestions" ? "cyan" : "gray"}
          padding={1}
        >
          <Text bold>Suggestions</Text>

          {isLoading ? (
            <Box marginTop={1} flexDirection="column">
              <Box>
                <Spinner type="dots" />
                <Text color="yellow"> {currentProgress}</Text>
              </Box>
              <Box marginTop={1} paddingX={1}>
                <Text color="gray" dimColor>
                  {currentProgress.includes("Generating")
                    ? "Claude is analyzing your config..."
                    : currentProgress.includes("GitHub")
                    ? "Fetching from community configs..."
                    : "Preparing suggestions..."}
                </Text>
              </Box>
            </Box>
          ) : result ? (
            <Box flexDirection="column" marginTop={1}>
              {/* Style Analysis */}
              {result.styleAnalysis && (
                <Box marginBottom={1}>
                  <Text color="cyan" bold>Style: </Text>
                  <Text color="gray">
                    {result.styleAnalysis.prefixPreference}, {result.styleAnalysis.navigationStyle}
                  </Text>
                </Box>
              )}

              {/* Scroll indicator - top */}
              {result.groups.length > VISIBLE_GROUPS && selectedGroup > 0 && (
                <Text color="gray">  ↑ {selectedGroup} more above</Text>
              )}

              {/* Visible groups only */}
              {visibleGroups.map(({ group, index }) => {
                const isSelected = index === selectedGroup;
                return (
                  <Box
                    key={index}
                    flexDirection="column"
                    marginBottom={1}
                    borderStyle={isSelected ? "double" : "single"}
                    borderColor={isSelected ? "cyanBright" : "gray"}
                    paddingX={1}
                  >
                    <Box>
                      <Text color={isSelected ? "cyanBright" : "gray"}>{isSelected ? "▶ " : "  "}</Text>
                      <Text bold color="green">{group.name}</Text>
                      <Text color="gray"> ({group.keybinds.length})</Text>
                    </Box>

                    {/* Show keybinds only for selected group to save space */}
                    {isSelected && group.keybinds.map((kb, ki) => (
                      <Box key={ki} marginLeft={2}>
                        <Text color="yellow" bold>{kb.keybind.padEnd(8)}</Text>
                        <Text color="gray"> {kb.description}</Text>
                      </Box>
                    ))}
                  </Box>
                );
              })}

              {/* Scroll indicator - bottom */}
              {result.groups.length > VISIBLE_GROUPS &&
               selectedGroup < result.groups.length - 1 && (
                <Text color="gray">  ↓ {result.groups.length - selectedGroup - 1} more below</Text>
              )}

              {/* Navigation help */}
              <Box marginTop={1}>
                <Text color="gray">
                  [{selectedGroup + 1}/{result.groups.length}] (j/k) navigate, (t) try in sandbox, (h) back
                </Text>
              </Box>
            </Box>
          ) : (
            <Text color="gray">Select a category and press Enter</Text>
          )}
        </Box>
      </Box>
    </Box>
  );
}
