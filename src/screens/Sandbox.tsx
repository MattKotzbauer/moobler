import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import Spinner from "ink-spinner";
import {
  isDockerAvailable,
  isImageBuilt,
  buildImage,
  launchSandbox,
  launchOverlay,
} from "../lib/docker.js";

interface Props {
  keybindsToTry: {
    keybinds: { keybind: string; command: string; description: string }[];
    groupName: string;
  } | null;
  notify: (msg: string) => void;
}

export function SandboxScreen({ keybindsToTry, notify }: Props) {
  const [status, setStatus] = useState("Ready");
  const [dockerOk, setDockerOk] = useState<boolean | null>(null);
  const [imageBuilt, setImageBuilt] = useState<boolean | null>(null);
  const [building, setBuilding] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  const log = (msg: string) => setLogs((l) => [...l.slice(-10), msg]);

  useEffect(() => {
    (async () => {
      const available = await isDockerAvailable();
      setDockerOk(available);
      if (available) {
        const built = await isImageBuilt();
        setImageBuilt(built);
      }
    })();
  }, []);

  useEffect(() => {
    if (keybindsToTry) {
      log(`Group: ${keybindsToTry.groupName} (${keybindsToTry.keybinds.length} keybinds)`);
    }
  }, [keybindsToTry]);

  const handleStart = async () => {
    if (!dockerOk) {
      notify("Docker not available");
      return;
    }

    if (!imageBuilt) {
      setBuilding(true);
      setStatus("Building image...");
      log("Building Docker image (first time only)...");
      try {
        await buildImage();
        setImageBuilt(true);
        log("Image built successfully!");
      } catch (e: any) {
        notify(`Build failed: ${e.message}`);
        setBuilding(false);
        return;
      }
      setBuilding(false);
    }

    // Launch overlay for guided keybind practice first
    if (keybindsToTry && keybindsToTry.keybinds.length > 0) {
      setStatus("Starting keybind practice...");
      log("Launching overlay for guided practice...");

      const overlayResult = await launchOverlay(keybindsToTry.keybinds);

      if (overlayResult.escaped) {
        setStatus("Practice cancelled");
        log("User pressed Escape - skipping sandbox");
        return;
      }

      if (overlayResult.error) {
        log(`Overlay error: ${overlayResult.error}`);
        // Continue to sandbox anyway
      } else if (overlayResult.completed) {
        log("Keybind practice complete!");
      }
    }

    // Now launch the sandbox for free practice
    setStatus("Launching sandbox...");
    log("Launching in Kitty...");

    const result = await launchSandbox({
      keybinds: keybindsToTry?.keybinds,
      description: keybindsToTry?.groupName,
    });

    if (result.success && result.terminal) {
      const termName = result.terminal.charAt(0).toUpperCase() + result.terminal.slice(1);
      setStatus(`Sandbox launched in ${termName}`);
      log(`Sandbox opened in new ${termName} window`);
      log("Exit tmux when done practicing");
    } else {
      setStatus("No supported terminal found");
      log("Could not find Kitty terminal");
      log("Install Kitty for sandbox support");
      notify("Kitty not found for sandbox");
    }
  };

  useInput((input) => {
    if (input === "s") {
      handleStart();
    }
  });

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Tmux Sandbox</Text>
      <Text color="gray">Try new keybindings in a safe containerized environment</Text>

      {/* Status */}
      <Box marginTop={1} borderStyle="single" borderColor="yellow" paddingX={1}>
        <Text bold>Status: </Text>
        {building ? (
          <>
            <Spinner type="dots" />
            <Text color="yellow"> {status}</Text>
          </>
        ) : (
          <Text color={dockerOk ? "green" : "red"}>{status}</Text>
        )}
      </Box>

      {/* Docker status */}
      <Box marginTop={1}>
        <Text>Docker: </Text>
        <Text color={dockerOk === true ? "green" : dockerOk === false ? "red" : "yellow"}>
          {dockerOk === null ? "Checking..." : dockerOk ? "Available" : "Not available"}
        </Text>
        {dockerOk && (
          <>
            <Text> | Image: </Text>
            <Text color={imageBuilt ? "green" : "yellow"}>
              {imageBuilt ? "Built" : "Not built"}
            </Text>
          </>
        )}
      </Box>

      {/* Keybinds to try */}
      <Box
        marginTop={1}
        borderStyle="single"
        borderColor="green"
        padding={1}
        flexDirection="column"
      >
        <Text bold color="green">
          Keybinds to Try
        </Text>
        {keybindsToTry ? (
          <>
            <Box>
              <Text bold>Group: </Text>
              <Text color="cyan">{keybindsToTry.groupName}</Text>
            </Box>
            <Box marginTop={1} flexDirection="column">
              {keybindsToTry.keybinds.map((kb, i) => (
                <Box key={i}>
                  <Text color="yellow" bold>{kb.keybind.padEnd(10)}</Text>
                  <Text color="gray"> {kb.description}</Text>
                </Box>
              ))}
            </Box>
          </>
        ) : (
          <Text color="gray">
            None selected - go to Discover (3) to pick a group
          </Text>
        )}
      </Box>

      {/* Logs */}
      <Box marginTop={1} flexDirection="column">
        <Text bold>Log</Text>
        <Box
          borderStyle="single"
          borderColor="gray"
          padding={1}
          flexDirection="column"
          height={8}
        >
          {logs.length === 0 ? (
            <Text color="gray">Press (s) to start sandbox</Text>
          ) : (
            logs.map((line, i) => (
              <Text key={i} color="gray">
                {line}
              </Text>
            ))
          )}
        </Box>
      </Box>

      {/* Controls */}
      <Box marginTop={1}>
        <Text color="gray">(s) Start sandbox</Text>
      </Box>
    </Box>
  );
}
