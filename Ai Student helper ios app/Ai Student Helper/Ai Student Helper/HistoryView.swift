//
//  HistoryView.swift
//  Ai Student Helper
//

import SwiftUI

struct HistoryView: View {
    @EnvironmentObject var viewModel: AppViewModel
    
    @State private var searchText = ""
    @State private var selectedFilter = "All"
    
    let filters = ["All", "Math", "Science", "Computer Science", "History", "English", "Other"]
    
    var filteredItems: [ChatSession] {
        viewModel.chatSessions.filter { item in
            let matchesSearch = searchText.isEmpty ||
                item.questionPreview.localizedCaseInsensitiveContains(searchText) ||
                item.answerPreview.localizedCaseInsensitiveContains(searchText)
            
            let matchesFilter = selectedFilter == "All" ||
                item.subject == selectedFilter
                
            return matchesSearch && matchesFilter
        }
    }
    
    // Helper to resolve SF symbol names matching models
    func getModelIcon(for modelName: String) -> String {
        switch modelName {
        case "Gemini": return "bolt.fill"
        case "Kimi": return "brain.fill"
        case "Mistral Large": return "sparkles.rectangle.stack.fill"
        case "Gemma 2B": return "cpu.fill"
        default: return "sparkles"
        }
    }
    
    // Helper to resolve colors matching models
    func getModelIconColor(for modelName: String) -> Color {
        switch modelName {
        case "Gemini": return .blue
        case "Kimi": return .orange
        case "Mistral Large": return .green
        case "Gemma 2B": return .pink
        default: return .purple
        }
    }
    
    var body: some View {
        VStack(spacing: 0) {
            
            // Header Section (Title & Count Badge)
            VStack(spacing: 16) {
                HStack(alignment: .center) {
                    Text("Chat History")
                        .font(.system(size: 28, weight: .black))
                        .foregroundColor(.white)
                    
                    Spacer()
                    
                    // Total conversations count badge
                    HStack(spacing: 6) {
                        Image(systemName: "bubble.left.and.bubble.right.fill")
                            .font(.system(size: 11))
                        Text("\(filteredItems.count)")
                            .font(.system(size: 12, weight: .bold))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(Color.appAccentTeal)
                    .cornerRadius(20)
                    .shadow(color: Color.appAccentTeal.opacity(0.3), radius: 6)
                }
                .padding(.horizontal, 20)
                .padding(.top, 20)
                
                // Search Bar
                HStack(spacing: 10) {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(Color.appSubtextGray)
                    
                    TextField("", text: $searchText)
                        .foregroundColor(.white)
                        .font(.system(size: 14, weight: .medium))
                        .placeholder(when: searchText.isEmpty) {
                            Text("Search past conversations...")
                                .foregroundColor(Color.appSubtextGray)
                                .font(.system(size: 14, weight: .medium))
                        }
                }
                .padding(.horizontal, 16)
                .frame(height: 48)
                .background(Color(hex: "#1A2230"))
                .cornerRadius(16)
                .padding(.horizontal, 20)
            }
            .padding(.bottom, 12)
            .background(Color.appBackground)
            
            // Filter Pills
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    ForEach(filters, id: \.self) { filter in
                        Button(action: {
                            withAnimation(.easeInOut(duration: 0.15)) {
                                selectedFilter = filter
                            }
                        }) {
                            Text(filter)
                                .font(.system(size: 13, weight: selectedFilter == filter ? .semibold : .medium))
                                .foregroundColor(selectedFilter == filter ? .white : Color.appSubtextGray)
                                .padding(.horizontal, 18)
                                .padding(.vertical, 8)
                                .background(selectedFilter == filter ? Color.appAccentTeal : Color(hex: "#1A2230"))
                                .cornerRadius(20)
                                .shadow(color: selectedFilter == filter ? Color.appAccentTeal.opacity(0.2) : .clear, radius: 4)
                        }
                    }
                }
                .padding(.horizontal, 20)
            }
            .padding(.bottom, 16)
            .background(Color.appBackground)
            
            // Chat List Cards
            ScrollView(.vertical, showsIndicators: false) {
                if filteredItems.isEmpty {
                    VStack(spacing: 12) {
                        Image(systemName: "clock.badge.exclamationmark")
                            .font(.system(size: 40))
                            .foregroundColor(Color.appSubtextGray)
                            .padding(.top, 60)
                        
                        Text("No history found")
                            .font(.system(size: 15, weight: .bold))
                            .foregroundColor(.white)
                        
                        Text("Try searching with different terms or select another filter tab.")
                            .font(.system(size: 13))
                            .foregroundColor(Color.appSubtextGray)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 32)
                    }
                } else {
                    LazyVStack(spacing: 16) {
                        ForEach(filteredItems) { item in
                            Button(action: {
                                viewModel.loadSession(id: item.id)
                            }) {
                                VStack(alignment: .leading, spacing: 12) {
                                    
                                    // Top Tag row
                                    HStack {
                                        Text(item.subject.uppercased())
                                            .font(.system(size: 9, weight: .bold))
                                            .foregroundColor(.white)
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 4)
                                            .background(Color.appAccentTeal)
                                            .cornerRadius(6)
                                        
                                        Spacer()
                                        
                                        Text(item.dateString)
                                            .font(.system(size: 11, weight: .medium))
                                            .foregroundColor(Color.appSubtextGray)
                                    }
                                    
                                    // Question and Answer Snippet
                                    VStack(alignment: .leading, spacing: 6) {
                                        Text(item.questionPreview)
                                            .font(.system(size: 16, weight: .bold))
                                            .foregroundColor(.white)
                                            .lineLimit(1)
                                            .frame(maxWidth: .infinity, alignment: .leading)
                                            .multilineTextAlignment(.leading)
                                        
                                        Text(item.answerPreview)
                                            .font(.system(size: 13))
                                            .foregroundColor(Color.appSubtextGray)
                                            .lineLimit(2)
                                            .lineSpacing(3)
                                            .frame(maxWidth: .infinity, alignment: .leading)
                                            .multilineTextAlignment(.leading)
                                    }
                                    
                                    // Divider
                                    Rectangle()
                                        .fill(Color.white.opacity(0.05))
                                        .frame(height: 1)
                                        .padding(.vertical, 2)
                                    
                                    // Bottom Model row
                                    HStack(spacing: 8) {
                                        Image(systemName: getModelIcon(for: item.modelName))
                                            .font(.system(size: 10))
                                            .foregroundColor(getModelIconColor(for: item.modelName))
                                        
                                        Text(item.modelName)
                                            .font(.system(size: 11, weight: .semibold))
                                            .foregroundColor(Color.white.opacity(0.8))
                                    }
                                }
                                .padding(20)
                                .background(Color.appCardBackground)
                                .cornerRadius(24)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 24)
                                        .stroke(Color.white.opacity(0.04), lineWidth: 1)
                                )
                            }
                            .buttonStyle(PlainButtonStyle())
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.bottom, 24)
                }
            }
            .background(Color.appBackground)
        }
        .preferredColorScheme(.dark)
    }
}

#Preview {
    HistoryView()
        .environmentObject(AppViewModel())
}
