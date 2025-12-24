import { createSignal, onMount } from 'solid-js';
import type { Component } from 'solid-js';
import { streamInsight, getProgress, updateProgress } from './api';
import { GhostMargin } from './components/GhostMargin';
import { DebugOverlay } from './components/DebugOverlay';
import './App.css';

const MOCK_CONTENT = `
  <h1>Chapter 3: Derivatives</h1>
  <p class="book-text">
    The derivative of a function of a real variable measures the sensitivity to change of the function value (output value) with respect to a change in its argument (input value).
  </p>
  <p class="book-text">
    The process of finding a derivative is called differentiation. The reverse process is called antidifferentiation. The fundamental theorem of calculus relates antidifferentiation with integration.
  </p>
  <p class="book-text">
    Let f be a real-valued function defined in an open neighborhood of a real number a. In classical geometry, the tangent line to the graph of the function f at a was the unique line through the point (a, f(a)) that did not meet the graph of f transversally, meaning that the line did not pass straight through the graph.
  </p>
  <div class="separator">* * *</div>
  <p class="book-text">
    Theorem 3.4 (Mean Value Theorem). Let f be a continuous function on the closed interval [a, b] and differentiable on the open interval (a, b). Then there exists a point c in (a, b) such that the tangent at c is parallel to the secant line through the endpoints.
  </p>
`;

const App: Component = () => {
  const [tokens, setTokens] = createSignal<string[]>([]);
  const [isThinking, setIsThinking] = createSignal(false);
  const [latency, setLatency] = createSignal<number>(0);

  let abortController: AbortController | null = null;
  const [progress, setProgress] = createSignal({ current_chapter: 1, current_page: 1 });

  // Debug State
  const [showDebug, setShowDebug] = createSignal(false);
  const [contextNodes, setContextNodes] = createSignal<any[]>([]);

  onMount(async () => {
    try {
      const p = await getProgress('calc101');
      setProgress(p);
      console.log("Loaded progress:", p);
    } catch (e) {
      console.error("Failed to load progress", e);
    }

    // Keyboard shortcut listener for Debug Toggle (Shift+T)
    window.addEventListener('keydown', (e) => {
      if (e.key === 'T' && e.shiftKey) {
        setShowDebug(prev => !prev);
      }
    });
  });

  const handleSelection = async () => {
    const selection = window.getSelection();
    if (!selection || selection.toString().length < 2) return;

    const text = selection.toString();

    // Reset state
    if (abortController) abortController.abort();
    abortController = new AbortController();
    setTokens([]);
    setIsThinking(true);
    setContextNodes([]);

    console.log("Selected:", text);

    await streamInsight(text, 3, 42, (event) => {
      if (event.type === 'meta') {
        const data = event.data as any;
        setLatency(data.latency_overhead);
        if (data.context_nodes) {
          setContextNodes(data.context_nodes); // Capture "thinking"
        }
      } else if (event.type === 'token') {
        setTokens(prev => [...prev, event.data]);
      } else if (event.type === 'done') {
        setIsThinking(false);
      }
    });

    // Assume interacting = updating progress (mock logic)
    await updateProgress('calc101', 3, 42);
    const p = await getProgress('calc101');
    setProgress(p);
  };

  return (
    <div class="app-container">
      <main class="pdf-view" onMouseUp={handleSelection}>
        <div class="progress-bar">
          Reading: Calculus 101 | Progress: Ch {progress().current_chapter} / Pg {progress().current_page}
          <span style={{ "margin-left": "20px", "font-size": "0.8em", color: "#666" }}>
            (Press Shift+T to inspect memory)
          </span>
        </div>
        <div innerHTML={MOCK_CONTENT} />

        <DebugOverlay visible={showDebug()} contextNodes={contextNodes()} />
      </main>

      <aside class="right-margin">
        <GhostMargin tokens={tokens()} isThinking={isThinking()} latency={latency()} />
      </aside>
    </div>
  );
};

export default App;
