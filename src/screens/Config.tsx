import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import { readTmuxConfig, parseTmuxConfig, type TmuxConfig } from "../lib/config.js";

interface Props {
  notify: (msg: string) => void;
}

export function ConfigScreen({ notify }: Props) {
  const [config, setConfig] = useState<TmuxConfig | null>(null);
  const [scrollOffset, setScrollOffset] = useState(0);
  const [tab, setTab] = useState<"bindings" | "style">("bindings");

  useEffect(() => {
    (async () => {
      const content = await readTmuxConfig();
      if (content) {
        setConfig(parseTmuxConfig(content));
      }
    })();
  }, []);

  useInput((input, key) => {
    if (input === "j" || key.downArrow) {
      setScrollOffset((o) => o + 1);
    } else if (input === "k" || key.upArrow) {
      setScrollOffset((o) => Math.max(0, o - 1));
    } else if (input === "h" || input === "l" || key.tab) {
      setTab((t) => (t === "bindings" ? "style" : "bindings"));
    }
  });

  if (!config) {
    return (
      <Box padding={1}>
        <Text color="yellow">No tmux.conf found at ~/.tmux.conf</Text>
      </Box>
    );
  }

  const visibleBindings = config.keybindings.slice(scrollOffset, scrollOffset + 15);

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Your tmux Configuration</Text>

      {/* Tabs */}
      <Box marginTop={1}>
        <Text
          color={tab === "bindings" ? "cyan" : "gray"}
          bold={tab === "bindings"}
        >
          [Keybindings]
        </Text>
        <Text> </Text>
        <Text color={tab === "style" ? "cyan" : "gray"} bold={tab === "style"}>
          [Style Analysis]
        </Text>
        <Text color="gray"> (h/l to switch)</Text>
      </Box>

      {tab === "bindings" ? (
        <Box flexDirection="column" marginTop={1}>
          <Box borderStyle="single" borderColor="blue" paddingX={1}>
            <Box width={15}>
              <Text bold color="green">
                Key
              </Text>
            </Box>
            <Box width={10}>
              <Text bold color="yellow">
                Mode
              </Text>
            </Box>
            <Box flexGrow={1}>
              <Text bold color="cyan">
                Command
              </Text>
            </Box>
          </Box>

          {visibleBindings.map((kb, i) => (
            <Box key={i} paddingX={1}>
              <Box width={15}>
                <Text color="green">{kb.key}</Text>
              </Box>
              <Box width={10}>
                <Text color={kb.mode === "root" ? "magenta" : "yellow"}>
                  {kb.mode}
                </Text>
              </Box>
              <Box flexGrow={1}>
                <Text>{kb.command.substring(0, 50)}</Text>
              </Box>
            </Box>
          ))}

          <Box marginTop={1}>
            <Text color="gray">
              Showing {scrollOffset + 1}-
              {Math.min(scrollOffset + 15, config.keybindings.length)} of{" "}
              {config.keybindings.length} (j/k to scroll)
            </Text>
          </Box>
        </Box>
      ) : (
        <Box flexDirection="column" marginTop={1} borderStyle="single" borderColor="blue" padding={1}>
          <Box>
            <Text bold>Prefix Preference: </Text>
            <Text color="cyan">{config.style.prefixPreference}</Text>
          </Box>
          <Box>
            <Text bold>Modifier Preference: </Text>
            <Text color="cyan">{config.style.modifierPreference}</Text>
          </Box>
          <Box>
            <Text bold>Navigation Style: </Text>
            <Text color="cyan">{config.style.navigationStyle}</Text>
          </Box>
          <Box marginTop={1}>
            <Text bold>Keys in Use: </Text>
          </Box>
          <Text color="gray" wrap="wrap">
            {config.style.keysInUse.slice(0, 20).join(", ")}
            {config.style.keysInUse.length > 20 ? "..." : ""}
          </Text>
        </Box>
      )}
    </Box>
  );
}
