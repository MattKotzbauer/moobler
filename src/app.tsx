import React, { useState, useEffect } from "react";
import { Box, Text, useApp, useInput } from "ink";
import { HomeScreen } from "./screens/Home.js";
import { DiscoverScreen } from "./screens/Discover.js";
import { SandboxScreen } from "./screens/Sandbox.js";
import { ConfigScreen } from "./screens/Config.js";
import { prewarmContainer } from "./lib/docker.js";

type Screen = "home" | "config" | "discover" | "sandbox";

export function App() {
  const { exit } = useApp();
  const [screen, setScreen] = useState<Screen>("home");
  const [notification, setNotification] = useState<string | null>(null);
  const [keybindToTry, setKeybindToTry] = useState<{
    keybind: string;
    command: string;
    description: string;
  } | null>(null);

  // Prewarm container on startup
  useEffect(() => {
    prewarmContainer().catch(() => {});
  }, []);

  // Clear notifications after 3 seconds
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => setNotification(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  // Global keybindings
  useInput((input, key) => {
    if (input === "q") {
      exit();
    } else if (input === "1") {
      setScreen("home");
    } else if (input === "2") {
      setScreen("config");
    } else if (input === "3") {
      setScreen("discover");
    } else if (input === "4") {
      setScreen("sandbox");
    } else if (input === "?") {
      setNotification("1:Home 2:Config 3:Discover 4:Sandbox q:Quit");
    }
  });

  const notify = (msg: string) => setNotification(msg);

  const tryKeybind = (kb: { keybind: string; command: string; description: string }) => {
    setKeybindToTry(kb);
    setScreen("sandbox");
  };

  return (
    <Box flexDirection="column" width="100%">
      {/* Header */}
      <Box borderStyle="single" borderColor="cyan" paddingX={1}>
        <Text bold color="cyan">
          moobler
        </Text>
        <Text color="gray"> - AI tmux tutor</Text>
        <Box flexGrow={1} />
        <Text color="gray">
          [1]Home [2]Config [3]Discover [4]Sandbox [q]Quit
        </Text>
      </Box>

      {/* Main content */}
      <Box flexGrow={1} flexDirection="column">
        {screen === "home" && (
          <HomeScreen setScreen={setScreen} notify={notify} />
        )}
        {screen === "config" && <ConfigScreen notify={notify} />}
        {screen === "discover" && (
          <DiscoverScreen notify={notify} tryKeybind={tryKeybind} />
        )}
        {screen === "sandbox" && (
          <SandboxScreen keybindToTry={keybindToTry} notify={notify} />
        )}
      </Box>

      {/* Notification bar */}
      {notification && (
        <Box borderStyle="single" borderColor="yellow" paddingX={1}>
          <Text color="yellow">{notification}</Text>
        </Box>
      )}
    </Box>
  );
}
