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
  tryKeybind: (kb: {
    keybind: string;
    command: string;
    description: string;
  }) => void;
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

export function DiscoverScreen({
  notify,
  tryKeybind,
  prefetchedResult,
  prefetchProgress,
  prefetchLoading,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState("");
  const [result, setResult] = useState<SuggestionResult | null>(null);
  const [selectedGroup, setSelectedGroup] = useState(0);
  const [selectedKeybind, setSelectedKeybind] = useState(0);
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
    // If selecting "All" and we have prefetched, just use it
    if (cat === "" && prefetchedResult) {
      setResult(prefetchedResult);
      setPanel("suggestions");
      setSelectedGroup(0);
      setSelectedKeybind(0);
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
      setSelectedKeybind(0);
      notify(`Found ${suggestions.groups.length} groups!`);
    } catch (e: any) {
      notify(`Error: ${e.message}`);
    } finally {
      setLoading(false);
      setProgress("");
    }
  };

  useInput((input, key) => {
    if (panel === "suggestions" && result) {
      const group = result.groups[selectedGroup];
      const keybinds = group?.keybinds || [];

      if (input === "h") {
        setPanel("categories");
      } else if (input === "j" || key.downArrow) {
        if (selectedKeybind < keybinds.length - 1) {
          setSelectedKeybind((k) => k + 1);
        } else if (selectedGroup < result.groups.length - 1) {
          setSelectedGroup((g) => g + 1);
          setSelectedKeybind(0);
        }
      } else if (input === "k" || key.upArrow) {
        if (selectedKeybind > 0) {
          setSelectedKeybind((k) => k - 1);
        } else if (selectedGroup > 0) {
          setSelectedGroup((g) => g - 1);
          const prevGroup = result.groups[selectedGroup - 1];
          setSelectedKeybind((prevGroup?.keybinds?.length || 1) - 1);
        }
      } else if (input === "t" || key.return) {
        const kb = keybinds[selectedKeybind];
        if (kb) {
          tryKeybind({
            keybind: kb.keybind,
            command: kb.command,
            description: kb.description,
          });
        }
      }
    } else if (input === "l" && !loading && !prefetchLoading) {
      if (result) {
        setPanel("suggestions");
      }
    } else if (input === "s" && !loading && !prefetchLoading) {
      fetchSuggestions(category);
    }
  });

  // Determine what loading state to show
  const isLoading = loading || (prefetchLoading && !result);
  const currentProgress = loading ? progress : prefetchProgress;

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
              {/* Show progress as greyed out thinking text */}
              <Box marginTop={1} paddingX={1}>
                <Text color="gray" dimColor>
                  {currentProgress.includes("Generating")
                    ? "Claude is analyzing your config and generating personalized suggestions..."
                    : currentProgress.includes("GitHub")
                    ? "Fetching popular keybindings from community configs..."
                    : currentProgress.includes("Analyzing")
                    ? "Detecting your preferred keybinding style..."
                    : "Preparing suggestions tailored to your setup..."}
                </Text>
              </Box>
            </Box>
          ) : result ? (
            <Box flexDirection="column" marginTop={1}>
              {/* Style Analysis */}
              {result.styleAnalysis && (
                <Box
                  borderStyle="single"
                  borderColor="blue"
                  paddingX={1}
                  marginBottom={1}
                >
                  <Text color="cyan" bold>
                    Your Style:{" "}
                  </Text>
                  <Text>
                    {result.styleAnalysis.prefixPreference},{" "}
                    {result.styleAnalysis.modifierPreference},{" "}
                    {result.styleAnalysis.navigationStyle}
                  </Text>
                </Box>
              )}

              {/* Groups */}
              {result.groups.map((group, gi) => (
                <Box key={gi} flexDirection="column" marginBottom={1}>
                  <Box
                    backgroundColor={gi === selectedGroup ? "blue" : undefined}
                    paddingX={1}
                  >
                    <Text bold color={gi === selectedGroup ? "white" : "green"}>
                      {group.name}
                    </Text>
                  </Box>
                  <Text color="gray" wrap="wrap">
                    {group.description}
                  </Text>

                  {/* Keybinds in group */}
                  {group.keybinds.map((kb, ki) => {
                    const isSelected = gi === selectedGroup && ki === selectedKeybind;
                    return (
                      <Box
                        key={ki}
                        paddingX={1}
                        backgroundColor={isSelected ? "blue" : undefined}
                      >
                        <Text
                          color={isSelected ? "white" : "yellow"}
                          bold
                        >
                          {kb.keybind}
                        </Text>
                        <Text color={isSelected ? "white" : undefined}>
                          {" "}- {kb.description}
                        </Text>
                      </Box>
                    );
                  })}
                </Box>
              ))}

              <Text color="gray">(t) Try selected, (h) back to categories</Text>
            </Box>
          ) : (
            <Text color="gray">Select a category and press Enter or (s)</Text>
          )}
        </Box>
      </Box>
    </Box>
  );
}
