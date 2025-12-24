import { For, Show } from 'solid-js';
import type { Component } from 'solid-js';

interface Props {
        contextNodes: any[];
        visible: boolean;
}

export const DebugOverlay: Component<Props> = (props) => {
        return (
                <Show when={props.visible}>
                        <div class="debug-overlay">
                                <h3>🧠 Preserved Thinking Cache (Active Memory)</h3>
                                <div class="nodes-list">
                                        <For each={props.contextNodes} fallback={<div class="empty">No context retrieved (Cold start)</div>}>
                                                {(node) => (
                                                        <div class="memory-node">
                                                                <div class="node-meta">
                                                                        <span class="badge">Ch {node.source_chapter}</span>
                                                                        <span class="badge">Pg {node.page_number}</span>
                                                                        <span class="type">{node.node_type}</span>
                                                                </div>
                                                                <div class="node-text">
                                                                        {node.text}
                                                                </div>
                                                        </div>
                                                )}
                                        </For>
                                </div>
                        </div>
                </Show>
        );
};
