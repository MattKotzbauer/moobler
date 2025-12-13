import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import Spinner from "ink-spinner";
import {
  isDockerAvailable,
  isImageBuilt,
  buildImage,
  launchSandbox,
} from "../lib/docker.js";
import { generateChallenge } from "../lib/ai.js";

interface Props {
  keybindToTry: {
    keybind: string;
    command: string;
    description: string;
  } | null;
  notify: (msg: string) => void;
}

export function SandboxScreen({ keybindToTry, notify }: Props) {
  const [status, setStatus] = useState("Ready");
  const [dockerOk, setDockerOk] = useState<boolean | null>(null);
  const [imageBuilt, setImageBuilt] = useState<boolean | null>(null);
  const [building, setBuilding] = useState(false);
  const [challenge, setChallenge] = useState<{
    objective: string;
    hint: string;
  } | null>(null);
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
    if (keybindToTry) {
      log(`Keybind to try: ${keybindToTry.keybind}`);
      generateChallenge(keybindToTry.keybind, keybindToTry.command).then(
        setChallenge
      );
    }
  }, [keybindToTry]);

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

    setStatus("Launching sandbox...");
    log("Launching sandbox in Kitty...");

    const launched = await launchSandbox({
      keybind: keybindToTry?.keybind,
      command: keybindToTry?.command,
      description: keybindToTry?.description,
    });

    if (launched) {
      setStatus("Sandbox launched in Kitty");
      log("Sandbox opened in new Kitty window");
      log("Exit tmux when done practicing");
    } else {
      setStatus("Could not launch Kitty");
      log("Kitty terminal not found");
      log("Install kitty or run Docker manually");
      notify("Kitty not found - install it for sandbox support");
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

      {/* Keybind to try */}
      <Box
        marginTop={1}
        borderStyle="single"
        borderColor="green"
        padding={1}
        flexDirection="column"
      >
        <Text bold color="green">
          Keybind to Try
        </Text>
        {keybindToTry ? (
          <>
            <Box>
              <Text bold>Key: </Text>
              <Text color="yellow">{keybindToTry.keybind}</Text>
            </Box>
            <Box>
              <Text bold>Command: </Text>
              <Text>{keybindToTry.command}</Text>
            </Box>
            <Box>
              <Text bold>Description: </Text>
              <Text color="gray">{keybindToTry.description}</Text>
            </Box>
          </>
        ) : (
          <Text color="gray">
            None selected - go to Discover (3) to pick one
          </Text>
        )}
      </Box>

      {/* Challenge */}
      {challenge && (
        <Box
          marginTop={1}
          borderStyle="single"
          borderColor="cyan"
          padding={1}
          flexDirection="column"
        >
          <Text bold color="cyan">
            Challenge
          </Text>
          <Box>
            <Text bold>Objective: </Text>
            <Text>{challenge.objective}</Text>
          </Box>
          <Box>
            <Text bold>Hint: </Text>
            <Text color="gray">{challenge.hint}</Text>
          </Box>
        </Box>
      )}

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
