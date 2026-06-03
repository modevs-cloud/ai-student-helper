//
//  ChatView.swift
//  Ai Student Helper
//

import SwiftUI

struct ChatView: View {
    @EnvironmentObject var viewModel: AppViewModel
    
    @State private var inputMessage = ""
    @State private var selectedSubject = "Math"
    @State private var selectedModel = "Groq Llama 3"
    
    let subjects = ["Math", "Science", "Computer Science", "History", "English", "Other"]
    let models = ["Groq Llama 3", "Gemini", "Kimi", "Mistral Large", "Gemma 2B"]
    
    // Dynamic Font Size Selection
    private var messageFontSize: CGFloat {
        switch viewModel.fontSizeSelection {
        case 0: return 12
        case 2: return 17
        default: return 14
        }
    }
    
    private var currentMessages: [CodableMessageItem] {
        viewModel.getActiveSessionMessages()
    }
    
    var body: some View {
        VStack(spacing: 0) {
            
            // Header
            VStack(spacing: 0) {
                HStack(spacing: 12) {
                    HStack(spacing: 8) {
                        ZStack {
                            RoundedRectangle(cornerRadius: 10)
                                .fill(Color.appAccentTeal)
                                .frame(width: 32, height: 32)
                            
                            Image(systemName: "graduationcap.fill")
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(width: 18, height: 18)
                                .foregroundColor(.white)
                        }
                        
                        Text("AI Student Helper")
                            .font(.system(size: 18, weight: .bold))
                            .foregroundColor(.white)
                            .tracking(-0.3)
                    }
                    
                    Spacer()
                    
                    HStack(spacing: 12) {
                        // New Chat Button
                        Button(action: {
                            viewModel.createNewChat()
                        }) {
                            Image(systemName: "plus")
                                .font(.system(size: 16, weight: .bold))
                                .foregroundColor(.white)
                                .frame(width: 36, height: 36)
                                .background(Color.appAccentTeal)
                                .clipShape(Circle())
                        }
                        
                        // User Initials Avatar Button
                        Button(action: {
                            viewModel.selectedTab = 3
                        }) {
                            ZStack {
                                Circle()
                                    .fill(Color(hex: "#0a5c5f"))
                                    .frame(width: 36, height: 36)
                                    .overlay(
                                        Circle()
                                            .stroke(Color.appAccentTeal, lineWidth: 1.5)
                                    )
                                
                                let initials = "\(viewModel.firstName.prefix(1))\(viewModel.lastName.prefix(1))"
                                Text(initials.isEmpty ? "AC" : initials)
                                    .font(.system(size: 13, weight: .bold))
                                    .foregroundColor(.white)
                            }
                        }
                        .buttonStyle(PlainButtonStyle())
                    }
                }
                .padding(.horizontal, 16)
                .padding(.top, 12)
                .padding(.bottom, 10)
                
                HStack(spacing: 10) {
                    HStack(spacing: 8) {
                        Menu {
                            ForEach(subjects, id: \.self) { sub in
                                Button(sub) {
                                    selectedSubject = sub
                                }
                            }
                        } label: {
                            HStack(spacing: 6) {
                                Image(systemName: "book.closed.fill")
                                    .font(.system(size: 10))
                                Text(selectedSubject)
                                    .font(.system(size: 11, weight: .semibold))
                                Image(systemName: "chevron.down")
                                    .font(.system(size: 8, weight: .bold))
                            }
                            .foregroundColor(.white)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(Color(hex: "#1A2230"))
                            .cornerRadius(16)
                            .overlay(
                                RoundedRectangle(cornerRadius: 16)
                                    .stroke(Color.white.opacity(0.05), lineWidth: 1)
                            )
                        }
                        
                        Menu {
                            ForEach(models, id: \.self) { model in
                                Button(model) {
                                    selectedModel = model
                                }
                            }
                        } label: {
                            HStack(spacing: 6) {
                                Image(systemName: "cpu.fill")
                                    .font(.system(size: 10))
                                Text(selectedModel)
                                    .font(.system(size: 11, weight: .semibold))
                                Image(systemName: "chevron.down")
                                    .font(.system(size: 8, weight: .bold))
                            }
                            .foregroundColor(.white)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(Color(hex: "#1A2230"))
                            .cornerRadius(16)
                            .overlay(
                                RoundedRectangle(cornerRadius: 16)
                                    .stroke(Color.white.opacity(0.05), lineWidth: 1)
                            )
                        }
                    }
                    
                    Spacer()
                    
                    // Clear Chat Button
                    Button(action: {
                        viewModel.clearHistory()
                    }) {
                        Image(systemName: "trash")
                            .font(.system(size: 14))
                            .foregroundColor(Color.appSubtextGray)
                            .frame(width: 32, height: 32)
                            .background(Color.white.opacity(0.02))
                            .cornerRadius(16)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 12)
            }
            .background(Color.appCardBackground)
            .overlay(
                Rectangle()
                    .fill(Color.white.opacity(0.05))
                    .frame(height: 1),
                alignment: .bottom
            )
            
            // Conversation Area
            ScrollViewReader { proxy in
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(spacing: viewModel.isCompactMessages ? 12 : 24) {
                        
                        if currentMessages.isEmpty {
                            // Blank state / Initial AI Greeting
                            VStack(spacing: 12) {
                                Image(systemName: "sparkles")
                                    .font(.system(size: 40))
                                    .foregroundColor(Color.appAccentTeal)
                                    .padding(.top, 48)
                                
                                Text("Start a new study conversation")
                                    .font(.system(size: 15, weight: .bold))
                                    .foregroundColor(.white)
                                
                                Text("Choose your subject and AI model above, then type a question to get instant step-by-step help.")
                                    .font(.system(size: 13))
                                    .foregroundColor(Color.appSubtextGray)
                                    .multilineTextAlignment(.center)
                                    .padding(.horizontal, 32)
                            }
                            .padding(.top, 40)
                        } else {
                            Text("Active Session")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(Color.appSubtextGray)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 4)
                                .background(Color(hex: "#1A2230"))
                                .cornerRadius(12)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(Color.white.opacity(0.05), lineWidth: 1)
                                )
                                .tracking(0.5)
                                .padding(.top, 16)
                            
                            ForEach(currentMessages) { msg in
                                if msg.isUser {
                                    HStack {
                                        Spacer()
                                        Text(msg.text)
                                            .font(.system(size: messageFontSize, weight: .medium))
                                            .foregroundColor(.white)
                                            .padding(.horizontal, 16)
                                            .padding(.vertical, viewModel.isCompactMessages ? 8 : 12)
                                            .background(Color.appAccentTeal)
                                            .cornerRadius(16)
                                            .padding(.leading, 40)
                                    }
                                } else {
                                    VStack(alignment: .leading, spacing: 6) {
                                        HStack(spacing: 8) {
                                            Text(msg.subject.uppercased())
                                                .font(.system(size: 9, weight: .bold))
                                                .foregroundColor(.white)
                                                .padding(.horizontal, 6)
                                                .padding(.vertical, 2)
                                                .background(Color.white.opacity(0.1))
                                                .cornerRadius(4)
                                            
                                            HStack(spacing: 4) {
                                                Image(systemName: "cpu")
                                                    .font(.system(size: 10))
                                                Text(msg.model)
                                                    .font(.system(size: 10, weight: .medium))
                                            }
                                            .foregroundColor(Color.appSubtextGray)
                                        }
                                        .padding(.leading, 4)
                                        
                                        VStack(alignment: .leading, spacing: 12) {
                                            Text(msg.text)
                                                .font(.system(size: messageFontSize))
                                                .foregroundColor(.white)
                                                .lineSpacing(4)
                                        }
                                        .padding(.horizontal, 16)
                                        .padding(.vertical, viewModel.isCompactMessages ? 8 : 14)
                                        .background(Color.appCardBackground)
                                        .cornerRadius(16)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 16)
                                                .stroke(Color.white.opacity(0.03), lineWidth: 1)
                                        )
                                        .padding(.trailing, 40)
                                    }
                                }
                            }
                            
                            if viewModel.isTyping {
                                VStack(alignment: .leading, spacing: 6) {
                                    HStack(spacing: 8) {
                                        Text(selectedSubject.uppercased())
                                            .font(.system(size: 9, weight: .bold))
                                            .foregroundColor(.white)
                                            .padding(.horizontal, 6)
                                            .padding(.vertical, 2)
                                            .background(Color.white.opacity(0.1))
                                            .cornerRadius(4)
                                        
                                        HStack(spacing: 4) {
                                            Image(systemName: "cpu")
                                                .font(.system(size: 10))
                                            Text(selectedModel)
                                                .font(.system(size: 10, weight: .medium))
                                        }
                                        .foregroundColor(Color.appSubtextGray)
                                    }
                                    .padding(.leading, 4)
                                    
                                    HStack(spacing: 4) {
                                        Circle()
                                            .fill(Color.white.opacity(0.6))
                                            .frame(width: 6, height: 6)
                                        Circle()
                                            .fill(Color.white.opacity(0.6))
                                            .frame(width: 6, height: 6)
                                        Circle()
                                            .fill(Color.white.opacity(0.6))
                                            .frame(width: 6, height: 6)
                                    }
                                    .padding(.horizontal, 16)
                                    .padding(.vertical, 14)
                                    .background(Color.appCardBackground)
                                    .cornerRadius(16)
                                }
                                .id("typingIndicator")
                            }
                        }
                        
                    }
                    .padding(.horizontal, 16)
                    .padding(.bottom, 24)
                    .onChange(of: currentMessages.count) { _ in
                        if let lastMessage = currentMessages.last {
                            withAnimation {
                                proxy.scrollTo(lastMessage.id, anchor: .bottom)
                            }
                        }
                    }
                    .onChange(of: viewModel.isTyping) { isTyping in
                        if isTyping {
                            withAnimation {
                                proxy.scrollTo("typingIndicator", anchor: .bottom)
                            }
                        }
                    }
                }
                .background(Color.appBackground)
            }
            
            // Input Message area
            VStack(spacing: 8) {
                HStack(spacing: 8) {
                    TextField("Ask anything about your studies...", text: $inputMessage)
                        .font(.system(size: 14))
                        .foregroundColor(.white)
                        .padding(.vertical, 12)
                        .padding(.horizontal, 16)
                        .background(Color(hex: "#1A2230"))
                        .cornerRadius(14)
                        .overlay(
                            RoundedRectangle(cornerRadius: 14)
                                .stroke(Color.white.opacity(0.05), lineWidth: 1)
                        )
                    
                    Button(action: {
                        guard !inputMessage.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
                        viewModel.sendMessage(text: inputMessage, subject: selectedSubject, model: selectedModel)
                        inputMessage = ""
                    }) {
                        Image(systemName: "paperplane.fill")
                            .font(.system(size: 14, weight: .bold))
                            .foregroundColor(.white)
                            .frame(width: 44, height: 44)
                            .background(Color.appAccentTeal)
                            .clipShape(Circle())
                    }
                }
                
                HStack {
                    Text("\(inputMessage.count) of 2000")
                        .font(.system(size: 10))
                        .foregroundColor(Color.appSubtextGray)
                    
                    Spacer()
                    
                    Text("AI responses may not always be accurate. Verify important information.")
                        .font(.system(size: 9))
                        .foregroundColor(Color.appSubtextGray)
                        .multilineTextAlignment(.trailing)
                }
                .padding(.horizontal, 4)
            }
            .padding(.horizontal, 16)
            .padding(.top, 12)
            .padding(.bottom, 16)
            .background(Color.appCardBackground)
            .overlay(
                Rectangle()
                    .fill(Color.white.opacity(0.05))
                    .frame(height: 1),
                alignment: .top
            )
            
        }
        .onAppear {
            if let activeId = viewModel.activeSessionId,
               let session = viewModel.chatSessions.first(where: { $0.id == activeId }) {
                selectedSubject = session.subject
                selectedModel = session.modelName
            } else {
                selectedSubject = viewModel.defaultSubject
                selectedModel = viewModel.preferredModel
            }
        }
        .onChange(of: viewModel.activeSessionId) { newId in
            if let activeId = newId,
               let session = viewModel.chatSessions.first(where: { $0.id == activeId }) {
                selectedSubject = session.subject
                selectedModel = session.modelName
            } else {
                selectedSubject = viewModel.defaultSubject
                selectedModel = viewModel.preferredModel
            }
        }
        .onChange(of: viewModel.defaultSubject) { newSubject in
            if viewModel.activeSessionId == nil {
                selectedSubject = newSubject
            }
        }
        .onChange(of: viewModel.preferredModel) { newModel in
            if viewModel.activeSessionId == nil {
                selectedModel = newModel
            }
        }
    }
}

#Preview {
    ChatView()
        .environmentObject(AppViewModel())
}
