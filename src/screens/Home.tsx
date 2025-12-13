import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import SelectInput from "ink-select-input";
import { readTmuxConfig, parseTmuxConfig } from "../lib/config.js";

const MOOBLER_ART = `
         /( ,,,,, )\\
        _\\,;;;;;;;,/_
     .-"; ;;;;;;;;; ;"-.
     '.__/\`_ / \\ _\`\\__.'
        | (')| |(') |
        | .--' '--. |
        |/ o     o \\|
        |           |
       / \\ _..=.._ / \\
      /:. '._____.'   \\
     ;::'    / \\      .;
     |     _|_ _|_   ::|
   .-|     '==o=='    '|-.
  /  |  . /       \\    |  \\
  |  | ::|         |   | .|
  |  (  ')         (.  )::|
  |: |   |; U U U ;|:: | \`|
  |' |   | \\ U U / |'  |  |
  ##V|   |_/\`"""\`\\_|   |V##
     ##V##         ##V##
`;

interface Props {
  setScreen: (screen: "home" | "config" | "discover" | "sandbox") => void;
  notify: (msg: string) => void;
}

export function HomeScreen({ setScreen, notify }: Props) {
  const [configStatus, setConfigStatus] = useState<string>("Checking...");
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    (async () => {
      const content = await readTmuxConfig();
      if (content) {
        const config = parseTmuxConfig(content);
        const styles: string[] = [];
        if (config.style.navigationStyle === "vim") styles.push("vim-style");
        if (config.style.prefixPreference === "no-prefix")
          styles.push("Alt/Meta bindings");
        setConfigStatus(
          `Found ~/.tmux.conf with ${config.keybindings.length} keybindings (${styles.join(", ") || "standard"})`
        );
      } else {
        setConfigStatus("No ~/.tmux.conf found - we'll help you create one!");
      }
    })();
  }, []);

  const items = [
    { label: "View My Config", value: "config" },
    { label: "Discover New Keybinds", value: "discover" },
    { label: "Try in Sandbox", value: "sandbox" },
  ];

  const handleSelect = (item: { value: string }) => {
    if (item.value === "config") setScreen("config");
    else if (item.value === "discover") setScreen("discover");
    else if (item.value === "sandbox") setScreen("sandbox");
  };

  useInput((input) => {
    if (input === "m") {
      notify("MOOBLER!");
    }
  });

  return (
    <Box flexDirection="column" padding={1}>
      {/* ASCII Art */}
      <Box>
        <Text color="green">{MOOBLER_ART}</Text>
      </Box>

      {/* Title */}
      <Box marginTop={1}>
        <Text bold color="cyan">
          moobler
        </Text>
      </Box>
      <Text color="gray">Learn new tmux controls with AI-powered suggestions</Text>

      {/* Config Status */}
      <Box
        marginTop={1}
        borderStyle="single"
        borderColor="blue"
        paddingX={1}
      >
        <Text>{configStatus}</Text>
      </Box>

      {/* Menu */}
      <Box marginTop={1} flexDirection="column">
        <SelectInput items={items} onSelect={handleSelect} />
      </Box>

      {/* Hint */}
      <Box marginTop={1}>
        <Text color="gray">Press ? for help, m for moobler</Text>
      </Box>
    </Box>
  );
}
