export interface StreamEvent {
        type: 'meta' | 'token' | 'done' | 'error';
        data?: any;
}

export async function getProgress(bookId: string) {
        const res = await fetch(`http://localhost:8000/progress/${bookId}`);
        return res.json();
}

export async function updateProgress(bookId: string, chapter: number, page: number) {
        await fetch('http://localhost:8000/progress', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                        book_id: bookId,
                        current_chapter: chapter,
                        current_page: page,
                        max_chapter_reached: chapter,
                        updated_at: 0
                })
        });
}

export async function streamInsight(
        text: string,
        chapter: number,
        page: number,
        onEvent: (event: StreamEvent) => void
) {
        try {
                const response = await fetch('http://localhost:8000/generate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                                selected_text: text,
                                current_chapter: chapter,
                                current_page: page
                        })
                });

                if (!response.ok) throw new Error('Network response was not ok');
                if (!response.body) throw new Error('No body');

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;

                        buffer += decoder.decode(value, { stream: true });
                        const lines = buffer.split('\n\n');
                        buffer = lines.pop() || '';

                        for (const line of lines) {
                                if (line.startsWith('event: ')) {
                                        const type = line.split('\n')[0].replace('event: ', '').trim();
                                        const dataStr = line.split('\n')[1]?.replace('data: ', '').trim();

                                        if (type === 'done') {
                                                onEvent({ type: 'done' });
                                                return;
                                        }

                                        try {
                                                const data = type === 'token' ? dataStr : JSON.parse(dataStr || '{}');
                                                onEvent({ type: type as any, data });
                                        } catch (e) {
                                                console.error("Parse error", e);
                                        }
                                }
                        }
                }
        } catch (err) {
                onEvent({ type: 'error', data: err });
        }
}
