import { useEffect, useState } from "react";
import { getTopics, getTopicChunks } from "../api/client";
import type { Topic, TopicDrillDown } from "../types";

export function useTopics() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selectedDrillDown, setSelectedDrillDown] = useState<TopicDrillDown | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getTopics()
      .then(setTopics)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, []);

  function selectTopic(topic: string) {
    setLoading(true);
    setError(null);
    getTopicChunks(topic)
      .then(setSelectedDrillDown)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }

  function clearSelection() {
    setSelectedDrillDown(null);
  }

  return { topics, selectedDrillDown, loading, error, selectTopic, clearSelection };
}
