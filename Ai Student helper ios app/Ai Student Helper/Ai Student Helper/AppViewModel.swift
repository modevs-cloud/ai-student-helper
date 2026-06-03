//
//  AppViewModel.swift
//  Ai Student Helper
//

import SwiftUI
import Combine

// Encapsulate API keys from .env file
struct APIKeys {
    static let groq = ""
    static let gemini = ""
    static let kimi = ""
    static let nvidia = ""
    static let gemma = ""
}

struct CodableMessageItem: Identifiable, Codable, Hashable {
    let id: UUID
    let text: String
    let isUser: Bool
    let time: String
    let subject: String
    let model: String
}

struct ChatSession: Identifiable, Codable, Hashable {
    let id: UUID
    let subject: String
    let modelName: String
    let dateString: String
    var messages: [CodableMessageItem]
    
    var questionPreview: String {
        messages.first(where: { $0.isUser })?.text ?? "No question yet"
    }
    
    var answerPreview: String {
        messages.first(where: { !$0.isUser })?.text ?? "No answers yet"
    }
}

class AppViewModel: ObservableObject {
    // Navigation / Tab bar Coordinator
    @Published var selectedTab: Int = 0
    
    // Auth State
    @Published var isLoggedIn: Bool {
        didSet { UserDefaults.standard.set(isLoggedIn, forKey: "isLoggedIn") }
    }
    
    // User Profile
    @Published var firstName: String {
        didSet { UserDefaults.standard.set(firstName, forKey: "firstName") }
    }
    @Published var lastName: String {
        didSet { UserDefaults.standard.set(lastName, forKey: "lastName") }
    }
    @Published var email: String {
        didSet { UserDefaults.standard.set(email, forKey: "email") }
    }
    
    // Preferences (Settings)
    @Published var defaultSubject: String {
        didSet { UserDefaults.standard.set(defaultSubject, forKey: "defaultSubject") }
    }
    @Published var preferredModel: String {
        didSet { UserDefaults.standard.set(preferredModel, forKey: "preferredModel") }
    }
    @Published var isDarkMode: Bool {
        didSet { UserDefaults.standard.set(isDarkMode, forKey: "isDarkMode") }
    }
    @Published var isCompactMessages: Bool {
        didSet { UserDefaults.standard.set(isCompactMessages, forKey: "isCompactMessages") }
    }
    @Published var fontSizeSelection: Int { // 0 = Small, 1 = Medium, 2 = Large
        didSet { UserDefaults.standard.set(fontSizeSelection, forKey: "fontSizeSelection") }
    }
    @Published var isStudyReminders: Bool {
        didSet { UserDefaults.standard.set(isStudyReminders, forKey: "isStudyReminders") }
    }
    @Published var isStreakAlerts: Bool {
        didSet { UserDefaults.standard.set(isStreakAlerts, forKey: "isStreakAlerts") }
    }
    
    // Statistics
    @Published var totalChats: Int {
        didSet { UserDefaults.standard.set(totalChats, forKey: "totalChats") }
    }
    @Published var questionsAsked: Int {
        didSet { UserDefaults.standard.set(questionsAsked, forKey: "questionsAsked") }
    }
    @Published var dayStreak: Int {
        didSet { UserDefaults.standard.set(dayStreak, forKey: "dayStreak") }
    }
    @Published var subjectsExplored: Set<String> {
        didSet {
            let arr = Array(subjectsExplored)
            UserDefaults.standard.set(arr, forKey: "subjectsExplored")
        }
    }
    
    // Live Sessions & History
    @Published var chatSessions: [ChatSession] = [] {
        didSet { saveSessions() }
    }
    @Published var activeSessionId: UUID? = nil
    @Published var isTyping: Bool = false
    
    init() {
        let loggedIn = UserDefaults.standard.bool(forKey: "isLoggedIn")
        let fName = UserDefaults.standard.string(forKey: "firstName") ?? ""
        let lName = UserDefaults.standard.string(forKey: "lastName") ?? ""
        let emailVal = UserDefaults.standard.string(forKey: "email") ?? ""
        let defSubject = UserDefaults.standard.string(forKey: "defaultSubject") ?? "Math"
        let prefModel = UserDefaults.standard.string(forKey: "preferredModel") ?? "Groq Llama 3"
        let dark = UserDefaults.standard.object(forKey: "isDarkMode") as? Bool ?? true
        let compact = UserDefaults.standard.bool(forKey: "isCompactMessages")
        let fontSel = UserDefaults.standard.object(forKey: "fontSizeSelection") as? Int ?? 1
        let reminders = UserDefaults.standard.object(forKey: "isStudyReminders") as? Bool ?? true
        let alerts = UserDefaults.standard.object(forKey: "isStreakAlerts") as? Bool ?? true
        
        let totalChatsVal = UserDefaults.standard.integer(forKey: "totalChats")
        let questionsAskedVal = UserDefaults.standard.integer(forKey: "questionsAsked")
        let dayStreakVal = UserDefaults.standard.integer(forKey: "dayStreak")
        let subjectsArr = UserDefaults.standard.stringArray(forKey: "subjectsExplored") ?? []
        let subjectsExploredVal = Set(subjectsArr)
        
        self._isLoggedIn = Published(wrappedValue: loggedIn)
        self._firstName = Published(wrappedValue: fName)
        self._lastName = Published(wrappedValue: lName)
        self._email = Published(wrappedValue: emailVal)
        self._defaultSubject = Published(wrappedValue: defSubject)
        self._preferredModel = Published(wrappedValue: prefModel)
        self._isDarkMode = Published(wrappedValue: dark)
        self._isCompactMessages = Published(wrappedValue: compact)
        self._fontSizeSelection = Published(wrappedValue: fontSel)
        self._isStudyReminders = Published(wrappedValue: reminders)
        self._isStreakAlerts = Published(wrappedValue: alerts)
        self._totalChats = Published(wrappedValue: totalChatsVal)
        self._questionsAsked = Published(wrappedValue: questionsAskedVal)
        self._dayStreak = Published(wrappedValue: dayStreakVal)
        self._subjectsExplored = Published(wrappedValue: subjectsExploredVal)
        
        loadSessions()
    }
    
    // MARK: - Actions
    
    func createNewChat() {
        activeSessionId = nil
        isTyping = false
    }
    
    func clearHistory() {
        chatSessions.removeAll()
        activeSessionId = nil
        totalChats = 0
        questionsAsked = 0
        dayStreak = 0
        subjectsExplored.removeAll()
    }
    
    func deleteAccount() {
        clearHistory()
        firstName = ""
        lastName = ""
        email = ""
        isLoggedIn = false
    }
    
    func loadSession(id: UUID) {
        activeSessionId = id
        selectedTab = 0 // Switch tab to Chat
    }
    
    func getActiveSessionMessages() -> [CodableMessageItem] {
        guard let activeId = activeSessionId else { return [] }
        return chatSessions.first(where: { $0.id == activeId })?.messages ?? []
    }
    
    // MARK: - API Dispatcher & Chat Logic
    
    func sendMessage(text: String, subject: String, model: String) {
        let timeFormatter = DateFormatter()
        timeFormatter.dateFormat = "h:mm a"
        let timeString = timeFormatter.string(from: Date())
        
        let newUserMessage = CodableMessageItem(
            id: UUID(),
            text: text,
            isUser: true,
            time: timeString,
            subject: subject,
            model: model
        )
        
        if activeSessionId == nil {
            // Create a new session
            let newSessionId = UUID()
            let dateFormatting = DateFormatter()
            dateFormatting.dateFormat = "MMM d, yyyy"
            
            let newSession = ChatSession(
                id: newSessionId,
                subject: subject,
                modelName: model,
                dateString: dateFormatting.string(from: Date()),
                messages: [newUserMessage]
            )
            chatSessions.insert(newSession, at: 0)
            activeSessionId = newSessionId
            totalChats += 1
        } else {
            // Append to existing session
            if let index = chatSessions.firstIndex(where: { $0.id == activeSessionId }) {
                chatSessions[index].messages.append(newUserMessage)
            }
        }
        
        // Increment Stats
        questionsAsked += 1
        subjectsExplored.insert(subject)
        
        // Trigger AI Completion
        isTyping = true
        performAIRequest(question: text, subject: subject, modelName: model)
    }
    
    private func performAIRequest(question: String, subject: String, modelName: String) {
        // Collect thread messages for conversation memory
        let sessionMessages = getActiveSessionMessages()
        var apiMessages: [[String: String]] = []
        
        // System Prompt matching app.py exactly
        let systemPrompt = """
        You are 'AI Student Helper' (also known as 'I Student Helper'), a premium AI-powered homework helper and study companion web application. Explain things simply, concisely, and clearly to the student. When answering math questions, use proper mathematical notation. For inline math use \\( ... \\) and for block/display equations use \\[ ... \\] so they render beautifully.
        Here is what you should know about this website:
        - Creator/Builder: This website was created and built by Mohammad as a helpful study companion project.
        - Purpose: To help students learn smarter and get instant, simplified explanations on academic subjects (Math, Science, History, English, CS).
        If a user asks who built this website or what it is, answer in a friendly, humble tone that it is an AI study companion created by Mohammad to help students learn. Do NOT explain deep backend tech stack implementation details, file databases, specific keys, or backend architecture. Keep all answers clean, brief, and student-focused.
        """
        apiMessages.append(["role": "system", "content": systemPrompt])
        
        // Map history (up to last 10 messages matching app.py's history limit)
        let lastTurns = sessionMessages.suffix(10)
        for msg in lastTurns {
            apiMessages.append([
                "role": msg.isUser ? "user" : "assistant",
                "content": msg.text
            ])
        }
        
        // Add current user message with subject prefix like app.py
        apiMessages.append([
            "role": "user",
            "content": "[\(subject)] \(question)"
        ])
        
        // Make request based on model, using identical fallback order as app.py
        Task {
            var reply: String? = nil
            
            // Fallback list of models based on user preference
            let fallbackModels: [String]
            switch modelName {
            case "Gemini":
                fallbackModels = ["Gemini", "Gemma 2B", "Mistral Large", "Groq Llama 3", "Kimi"]
            case "Kimi":
                fallbackModels = ["Kimi", "Gemma 2B", "Mistral Large", "Groq Llama 3", "Gemini"]
            case "Mistral Large":
                fallbackModels = ["Mistral Large", "Gemma 2B", "Groq Llama 3", "Gemini", "Kimi"]
            case "Gemma 2B":
                fallbackModels = ["Gemma 2B", "Mistral Large", "Groq Llama 3", "Gemini", "Kimi"]
            default: // Groq Llama 3
                fallbackModels = ["Groq Llama 3", "Gemma 2B", "Mistral Large", "Gemini", "Kimi"]
            }
            
            var lastErrorMsg = "Unknown error"
            
            for attemptModel in fallbackModels {
                do {
                    print("DEBUG: Requesting model: \(attemptModel)")
                    if attemptModel == "Gemini" {
                        reply = try await fetchGeminiCompletion(messages: apiMessages)
                    } else if attemptModel == "Kimi" {
                        reply = try await fetchKimiCompletion(messages: apiMessages)
                    } else if attemptModel == "Mistral Large" {
                        reply = try await fetchNvidiaCompletion(model: "mistralai/mistral-large-3-675b-instruct-2512", key: APIKeys.nvidia, messages: apiMessages)
                    } else if attemptModel == "Gemma 2B" {
                        reply = try await fetchNvidiaCompletion(model: "google/gemma-2-2b-it", key: APIKeys.gemma, messages: apiMessages)
                    } else { // Groq Llama 3
                        reply = try await fetchGroqCompletion(messages: apiMessages)
                    }
                    
                    if let r = reply, !r.isEmpty {
                        break
                    }
                } catch {
                    print("DEBUG: Model \(attemptModel) failed: \(error.localizedDescription)")
                    lastErrorMsg = error.localizedDescription
                }
            }
            
            let finalReply = reply ?? "⚠️ Could not get an AI answer. Please check that your API keys are correctly set in the .env file and restart the server (Last error: \(lastErrorMsg))."
            
            await MainActor.run {
                let timeFormatter = DateFormatter()
                timeFormatter.dateFormat = "h:mm a"
                let responseTime = timeFormatter.string(from: Date())
                
                let aiResponse = CodableMessageItem(
                    id: UUID(),
                    text: finalReply,
                    isUser: false,
                    time: responseTime,
                    subject: subject,
                    model: modelName
                )
                
                if let index = self.chatSessions.firstIndex(where: { $0.id == self.activeSessionId }) {
                    self.chatSessions[index].messages.append(aiResponse)
                }
                self.isTyping = false
            }
        }
    }
    
    // MARK: - Native URLSession Fetch Requests
    
    private func fetchGroqCompletion(messages: [[String: String]]) async throws -> String {
        let url = URL(string: "https://api.groq.com/openai/v1/chat/completions")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(APIKeys.groq)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "max_tokens": 4000
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw NSError(domain: "Groq", code: (response as? HTTPURLResponse)?.statusCode ?? 500)
        }
        
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        let choices = json?["choices"] as? [[String: Any]]
        let message = choices?.first?["message"] as? [String: Any]
        return (message?["content"] as? String ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
    }
    
    private func fetchGeminiCompletion(messages: [[String: String]]) async throws -> String {
        let url = URL(string: "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=\(APIKeys.gemini)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Convert OpenAI chat messages to Gemini contents structure by prepending system instructions to first user turn, matching app.py exactly
        var contents: [[String: Any]] = []
        var systemText = ""
        
        for msg in messages {
            let role = msg["role"] ?? ""
            let content = msg["content"] ?? ""
            
            if role == "system" {
                systemText = content
            } else if role == "user" {
                let text = systemText.isEmpty ? content : "\(systemText)\n\n\(content)"
                contents.append([
                    "role": "user",
                    "parts": [["text": text]]
                ])
                systemText = "" // Only prepend once
            } else if role == "assistant" {
                contents.append([
                    "role": "model",
                    "parts": [["text": content]]
                ])
            }
        }
        
        let body: [String: Any] = ["contents": contents]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw NSError(domain: "Gemini", code: (response as? HTTPURLResponse)?.statusCode ?? 500)
        }
        
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        let candidates = json?["candidates"] as? [[String: Any]]
        let content = candidates?.first?["content"] as? [String: Any]
        let parts = content?["parts"] as? [[String: Any]]
        return (parts?.first?["text"] as? String ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
    }
    
    private func fetchKimiCompletion(messages: [[String: String]]) async throws -> String {
        let url = URL(string: "https://api.moonshot.cn/v1/chat/completions")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(APIKeys.kimi)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "model": "moonshot-v1-8k",
            "messages": messages,
            "max_tokens": 4000
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw NSError(domain: "Kimi", code: (response as? HTTPURLResponse)?.statusCode ?? 500)
        }
        
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        let choices = json?["choices"] as? [[String: Any]]
        let message = choices?.first?["message"] as? [String: Any]
        return (message?["content"] as? String ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
    }
    
    private func fetchNvidiaCompletion(model: String, key: String, messages: [[String: String]]) async throws -> String {
        let url = URL(string: "https://integrate.api.nvidia.com/v1/chat/completions")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(key)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "model": model,
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.15,
            "top_p": 1.0
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw NSError(domain: "Nvidia", code: (response as? HTTPURLResponse)?.statusCode ?? 500)
        }
        
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        let choices = json?["choices"] as? [[String: Any]]
        let message = choices?.first?["message"] as? [String: Any]
        return (message?["content"] as? String ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
    }
    
    // MARK: - Storage Helpers
    
    private func saveSessions() {
        if let encoded = try? JSONEncoder().encode(chatSessions) {
            UserDefaults.standard.set(encoded, forKey: "chatSessions")
        }
    }
    
    private func loadSessions() {
        if let data = UserDefaults.standard.data(forKey: "chatSessions"),
           let decoded = try? JSONDecoder().decode([ChatSession].self, from: data) {
            self.chatSessions = decoded
        }
    }
    
    private func seedInitialSessions() {
        let sessions = [
            ChatSession(
                id: UUID(),
                subject: "Math",
                modelName: "Groq Llama 3",
                dateString: "Today",
                messages: [
                    CodableMessageItem(
                        id: UUID(),
                        text: "How to solve quadratic equations using the formula?",
                        isUser: true,
                        time: "10:41 AM",
                        subject: "Math",
                        model: "Groq Llama 3"
                    ),
                    CodableMessageItem(
                        id: UUID(),
                        text: "To solve a quadratic equation of the form \\( ax^2 + bx + c = 0 \\), you can use the quadratic formula:\n\n\\[ x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a} \\]\n\nFirst, identify the coefficients \\( a \\), \\( b \\), and \\( c \\), substitute them into the formula, and evaluate.",
                        isUser: false,
                        time: "10:42 AM",
                        subject: "Math",
                        model: "Groq Llama 3"
                    )
                ]
            ),
            ChatSession(
                id: UUID(),
                subject: "History",
                modelName: "Kimi",
                dateString: "Yesterday",
                messages: [
                    CodableMessageItem(
                        id: UUID(),
                        text: "Main causes of World War I",
                        isUser: true,
                        time: "2:15 PM",
                        subject: "History",
                        model: "Kimi"
                    ),
                    CodableMessageItem(
                        id: UUID(),
                        text: "The outbreak of World War I in 1914 was the result of a complex web of factors, often remembered by the acronym MAIN:\n\n1. **Militarism**: The arms race between European powers.\n2. **Alliances**: Mutual defense pacts binding countries together.\n3. **Imperialism**: Competition for foreign colonies.\n4. **Nationalism**: Intense national pride and territorial conflicts.",
                        isUser: false,
                        time: "2:16 PM",
                        subject: "History",
                        model: "Kimi"
                    )
                ]
            ),
            ChatSession(
                id: UUID(),
                subject: "Computer Science",
                modelName: "Gemini",
                dateString: "Oct 12, 2023",
                messages: [
                    CodableMessageItem(
                        id: UUID(),
                        text: "Explain recursion in Python with an example",
                        isUser: true,
                        time: "9:05 AM",
                        subject: "Computer Science",
                        model: "Gemini"
                    ),
                    CodableMessageItem(
                        id: UUID(),
                        text: "Recursion is a programming technique where a function calls itself to solve smaller instances of the same problem. A classic example is calculating the factorial of a number:\n\n```python\ndef factorial(n):\n    if n == 1: # Base case\n        return 1\n    else:\n        return n * factorial(n - 1)\n```",
                        isUser: false,
                        time: "9:07 AM",
                        subject: "Computer Science",
                        model: "Gemini"
                    )
                ]
            ),
            ChatSession(
                id: UUID(),
                subject: "English",
                modelName: "Mistral Large",
                dateString: "Oct 10, 2023",
                messages: [
                    CodableMessageItem(
                        id: UUID(),
                        text: "Symbolism of the green light in The Great Gatsby",
                        isUser: true,
                        time: "4:32 PM",
                        subject: "English",
                        model: "Mistral Large"
                    ),
                    CodableMessageItem(
                        id: UUID(),
                        text: "In F. Scott Fitzgerald's novel, the green light at the end of Daisy's dock represents Gatsby's unattainable dream, his hopes for the future, and the broader American Dream. It is a guiding star that...",
                        isUser: false,
                        time: "4:34 PM",
                        subject: "English",
                        model: "Mistral Large"
                    )
                ]
            )
        ]
        self.chatSessions = sessions
    }
}
