import { For, createEffect } from 'solid-js';
import type { Component } from 'solid-js';
import './GhostMargin.css';

interface Props {
        tokens: string[];
        isThinking: boolean;
        latency?: number;
}

export const GhostMargin: Component<Props> = (props) => {
        let containerRef: HTMLDivElement | undefined;

        createEffect(() => {
                // Scroll to bottom effect if needed, but for margin we usually want it to flow naturally
                if (containerRef) {
                        // logic to keep view in sync
                }
        });

        return (
                <div class="ghost-margin" ref={containerRef}>
                        <div class="margin-header">
                                <span class="indicator">
                                        {props.isThinking ? 'Reading...' : ' Insight'}
                                </span>
                                {props.latency && <span class="latency">{props.latency.toFixed(0)}ms</span>}
                        </div>

                        <div class="margin-content">
                                <For each={props.tokens}>
                                        {(token, i) => (
                                                <span
                                                        class="scan-in"
                                                        style={{ "animation-delay": `${i() * 10}ms` }}
                                                >
                                                        {token}
                                                </span>
                                        )}
                                </For>
                                {props.isThinking && <span class="cursor">|</span>}
                        </div>
                </div>
        );
};
