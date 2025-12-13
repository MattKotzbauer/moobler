import React, { useState } from "react";
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
}

const CATEGORIES = [
  { label: "Navigation", value: "navigation" },
  { label: "Pane Management", value: "panes" },
  { label: "Window Management", value: "windows" },
  { label: "Session Management", value: "sessions" },
  { label: "Copy Mode", value: "copy" },
  { label: "Productivity", value: "productivity" },
];

export function DiscoverScreen({ notify, tryKeybind }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SuggestionResult | null>(null);
  const [selectedGroup, setSelectedGroup] = useState(0);
  const [selectedKeybind, setSelectedKeybind] = useState(0);
  const [panel, setPanel] = useState<"categories" | "suggestions">("categories");
  const [category, setCategory] = useState("navigation");

  const fetchSuggestions = async (cat: string) => {
    setLoading(true);
    setCategory(cat);
    try {
      const suggestions = await getAISuggestions(cat);
      setResult(suggestions);
      setPanel("suggestions");
      setSelectedGroup(0);
      setSelectedKeybind(0);
      notify(`Found ${suggestions.groups.length} groups!`);
    } catch (e: any) {
      notify(`Error: ${e.message}`);
    } finally {
      setLoading(false);
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
    } else if (input === "l" && !loading) {
      if (result) {
        setPanel("suggestions");
      }
    } else if (input === "s" && !loading) {
      fetchSuggestions(category);
    }
  });

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
            isFocused={panel === "categories" && !loading}
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

          {loading ? (
            <Box marginTop={1}>
              <Spinner type="dots" />
              <Text color="yellow"> Analyzing your config + GitHub...</Text>
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
                    <Text bold color="green">
                      {group.name}
                    </Text>
                  </Box>
                  <Text color="gray" wrap="wrap">
                    {group.description}
                  </Text>

                  {/* Keybinds in group */}
                  {group.keybinds.map((kb, ki) => (
                    <Box
                      key={ki}
                      paddingX={1}
                      backgroundColor={
                        gi === selectedGroup && ki === selectedKeybind
                          ? "cyan"
                          : undefined
                      }
                    >
                      <Text
                        color={
                          gi === selectedGroup && ki === selectedKeybind
                            ? "black"
                            : "yellow"
                        }
                        bold
                      >
                        {kb.keybind}
                      </Text>
                      <Text
                        color={
                          gi === selectedGroup && ki === selectedKeybind
                            ? "black"
                            : undefined
                        }
                      >
                        {" "}
                        - {kb.description}
                      </Text>
                    </Box>
                  ))}
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
