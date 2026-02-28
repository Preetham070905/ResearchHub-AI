import axios, { type AxiosInstance } from 'axios';
import type {
    TokenResponse,
    Workspace,
    ChatResponse,
    AnalysisHistoryItem,
    PaperItem,
    AgentResponse,
    ConversationItem,
    SearchPaper,
} from '../types/api';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
    private http: AxiosInstance;

    constructor() {
        this.http = axios.create({ baseURL: BASE_URL, timeout: 120_000 }); // 2 min timeout for analysis pipeline
        this.http.interceptors.request.use((config) => {
            const token = localStorage.getItem('token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        });
    }

    // ── Auth ──────────────────────────────────────────────
    async login(email: string, password: string): Promise<TokenResponse> {
        const form = new URLSearchParams();
        form.append('username', email);
        form.append('password', password);
        const { data } = await this.http.post<TokenResponse>('/auth/login', form, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        return data;
    }

    async register(email: string, password: string): Promise<{ message: string }> {
        const { data } = await this.http.post('/auth/register', { email, password });
        return data;
    }

    // ── Workspaces ────────────────────────────────────────
    async listWorkspaces(): Promise<Workspace[]> {
        const { data } = await this.http.get<Workspace[]>('/workspaces/');
        return data;
    }

    async createWorkspace(name: string): Promise<Workspace> {
        const { data } = await this.http.post<Workspace>('/workspaces/', { name });
        return data;
    }

    async updateWorkspace(id: number, name: string): Promise<Workspace> {
        const { data } = await this.http.patch<Workspace>(`/workspaces/${id}`, { name });
        return data;
    }

    async deleteWorkspace(id: number): Promise<void> {
        await this.http.delete(`/workspaces/${id}`);
    }

    // ── Full Pipeline Analysis ─────────────────────────────
    async runAnalysis(query: string, workspaceId?: number): Promise<ChatResponse> {
        const { data } = await this.http.post<ChatResponse>('/chat/analyze', {
            query,
            workspace_id: workspaceId ?? null,
        });
        return data;
    }

    async getHistory(workspaceId: number): Promise<AnalysisHistoryItem[]> {
        const { data } = await this.http.get<AnalysisHistoryItem[]>(
            `/chat/history/${workspaceId}`
        );
        return data;
    }

    async getResult(analysisId: number): Promise<{ result: Record<string, unknown> }> {
        const { data } = await this.http.get(`/chat/result/${analysisId}`);
        return data;
    }

    async getConversations(workspaceId: number): Promise<ConversationItem[]> {
        const { data } = await this.http.get<ConversationItem[]>(
            `/chat/conversations/${workspaceId}`
        );
        return data;
    }

    // ── Papers ────────────────────────────────────────────
    async uploadPaper(workspaceId: number, file: File): Promise<PaperItem> {
        const form = new FormData();
        form.append('file', file);
        const { data } = await this.http.post<PaperItem>(
            `/papers/${workspaceId}`,
            form,
            { headers: { 'Content-Type': 'multipart/form-data' } }
        );
        return data;
    }

    async listPapers(workspaceId: number): Promise<PaperItem[]> {
        const { data } = await this.http.get<PaperItem[]>(`/papers/${workspaceId}`);
        return data;
    }

    async deletePaper(workspaceId: number, paperId: number): Promise<void> {
        await this.http.delete(`/papers/${workspaceId}/${paperId}`);
    }

    async importPaper(workspaceId: number, paper: SearchPaper): Promise<PaperItem> {
        const { data } = await this.http.post<PaperItem>(
            `/papers/${workspaceId}/import`,
            {
                title: paper.title,
                authors: paper.authors,
                abstract: paper.abstract,
                year: paper.year,
                source: paper.source,
                url: paper.url,
            }
        );
        return data;
    }

    getDownloadUrl(workspaceId: number, paperId: number): string {
        return `${BASE_URL}/papers/${workspaceId}/${paperId}/download`;
    }

    // ── Individual Agent Endpoints ────────────────────────
    async searchPapers(query: string, maxResults = 5): Promise<AgentResponse> {
        const { data } = await this.http.post<AgentResponse>('/agents/search-papers', {
            query, max_results: maxResults,
        });
        return data;
    }

    async agentSummarize(query: string): Promise<AgentResponse> {
        const { data } = await this.http.post<AgentResponse>('/agents/summarize', { query });
        return data;
    }

    async agentCompare(query: string): Promise<AgentResponse> {
        const { data } = await this.http.post<AgentResponse>('/agents/compare', { query });
        return data;
    }

    async agentInsights(query: string): Promise<AgentResponse> {
        const { data } = await this.http.post<AgentResponse>('/agents/insights', { query });
        return data;
    }

    async agentGaps(query: string): Promise<AgentResponse> {
        const { data } = await this.http.post<AgentResponse>('/agents/gaps', { query });
        return data;
    }

    async agentTrends(query: string): Promise<AgentResponse> {
        const { data } = await this.http.post<AgentResponse>('/agents/trends', { query });
        return data;
    }

    async agentNovelty(query: string): Promise<AgentResponse> {
        const { data } = await this.http.post<AgentResponse>('/agents/novelty', { query });
        return data;
    }

    async agentCritique(query: string): Promise<AgentResponse> {
        const { data } = await this.http.post<AgentResponse>('/agents/critique', { query });
        return data;
    }

    async agentRoadmap(query: string): Promise<AgentResponse> {
        const { data } = await this.http.post<AgentResponse>('/agents/roadmap', { query });
        return data;
    }

    async agentLiteratureReview(query: string): Promise<AgentResponse> {
        const { data } = await this.http.post<AgentResponse>('/agents/literature-review', { query });
        return data;
    }

    async agentKnowledgeGraph(query: string): Promise<AgentResponse> {
        const { data } = await this.http.post<AgentResponse>('/agents/knowledge-graph', { query });
        return data;
    }

    async agentRouteIntent(query: string): Promise<AgentResponse> {
        const { data } = await this.http.post<AgentResponse>('/agents/route-intent', { query });
        return data;
    }
}

const api = new ApiClient();
export default api;
