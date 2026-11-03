import type { AiTool } from '@iobroker/ai-gui';

/**
 * Documentation search as a tool for the AI chat of an ioBroker editor.
 * The tool runs in the browser, so the service must allow the origin of the editor (IOB_RAG_CORS).
 * If the service is protected with IOB_RAG_TOKEN, pass the same token here. It is visible to every user
 * of the editor, so it only keeps other clients on the network away, not the editor's users.
 */
export function searchIoBrokerDocsTool(baseUrl: string, token?: string): AiTool {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    return {
        definition: {
            type: 'function',
            function: {
                name: 'search_iobroker_docs',
                description:
                    'Search ioBroker documentation and source code. Results describe ioBroker, not this installation.',
                parameters: {
                    type: 'object',
                    properties: {
                        question: { type: 'string', description: 'What to look up' },
                        top_k: { type: 'integer', description: 'Number of results, default 5' },
                    },
                    required: ['question'],
                },
            },
        },
        run: async args => {
            const response = await fetch(`${baseUrl}/query`, {
                method: 'POST',
                headers,
                body: JSON.stringify({ question: String(args.question), top_k: Number(args.top_k) || 5 }),
            });
            if (!response.ok) {
                return `Documentation search failed with status ${response.status}`;
            }
            const answer = (await response.json()) as { context: string };
            return answer.context || 'No results.';
        },
    };
}
