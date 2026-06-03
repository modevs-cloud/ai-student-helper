//
//  SettingsView.swift
//  Ai Student Helper
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var viewModel: AppViewModel
    @State private var showingSaveAlert = false
    
    let subjects = ["Math", "Science", "Computer Science", "History", "English", "Other"]
    
    struct ModelOption: Identifiable {
        let id = UUID()
        let name: String
        let desc: String
    }
    
    let modelOptions = [
        ModelOption(name: "Groq Llama 3", desc: "Lightning Fast"),
        ModelOption(name: "Gemini", desc: "Balanced"),
        ModelOption(name: "Kimi", desc: "Deep Reasoning"),
        ModelOption(name: "Mistral Large", desc: "Complex Tasks"),
        ModelOption(name: "Gemma 2B", desc: "Lightweight")
    ]
    
    var body: some View {
        ZStack {
            Color.appBackground.ignoresSafeArea()
            
            VStack(spacing: 0) {
                // Header (Settings Title & Save Changes Button)
                HStack {
                    Text("Settings")
                        .font(.system(size: 28, weight: .black))
                        .foregroundColor(.white)
                    
                    Spacer()
                    
                    Button(action: {
                        showingSaveAlert = true
                    }) {
                        Text("Save Changes")
                            .font(.system(size: 13, weight: .bold))
                            .foregroundColor(.white)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(Color.appAccentTeal)
                            .cornerRadius(18)
                            .shadow(color: Color.appAccentTeal.opacity(0.3), radius: 6)
                    }
                }
                .padding(.horizontal, 20)
                .padding(.top, 20)
                .padding(.bottom, 20)
                
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(spacing: 24) {
                        
                        // 1. Learning Preferences
                        VStack(alignment: .leading, spacing: 10) {
                            Text("LEARNING PREFERENCES")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(Color.appSubtextGray)
                                .tracking(0.8)
                                .padding(.leading, 4)
                            
                            VStack(spacing: 0) {
                                // Default Subject Dropdown
                                HStack(spacing: 12) {
                                    // Icon Box
                                    ZStack {
                                        RoundedRectangle(cornerRadius: 10)
                                            .fill(Color.white.opacity(0.03))
                                            .frame(width: 38, height: 38)
                                        
                                        Image(systemName: "book.closed.fill")
                                            .font(.system(size: 14))
                                            .foregroundColor(Color.appAccentTeal)
                                    }
                                    
                                    Text("Default Subject")
                                        .font(.system(size: 15, weight: .semibold))
                                        .foregroundColor(.white)
                                    
                                    Spacer()
                                    
                                    Menu {
                                        ForEach(subjects, id: \.self) { sub in
                                            Button(sub) {
                                                viewModel.defaultSubject = sub
                                            }
                                        }
                                    } label: {
                                        HStack(spacing: 8) {
                                            Text(viewModel.defaultSubject)
                                                .font(.system(size: 13, weight: .semibold))
                                                .foregroundColor(.white.opacity(0.8))
                                            
                                            Image(systemName: "chevron.up.chevron.down")
                                                .font(.system(size: 10))
                                                .foregroundColor(Color.appSubtextGray)
                                        }
                                        .padding(.horizontal, 14)
                                        .padding(.vertical, 8)
                                        .background(Color(hex: "#1A2230"))
                                        .cornerRadius(10)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 10)
                                                .stroke(Color.white.opacity(0.05), lineWidth: 1)
                                        )
                                    }
                                }
                                .padding(16)
                                
                                Divider()
                                    .background(Color.white.opacity(0.04))
                                    .padding(.horizontal, 16)
                                
                                // Preferred AI Model
                                VStack(alignment: .leading, spacing: 14) {
                                    HStack(spacing: 12) {
                                        // Icon Box
                                        ZStack {
                                            RoundedRectangle(cornerRadius: 10)
                                                .fill(Color.white.opacity(0.03))
                                                .frame(width: 38, height: 38)
                                            
                                            Image(systemName: "cpu.fill")
                                                .font(.system(size: 14))
                                                .foregroundColor(Color.appAccentTeal)
                                        }
                                        
                                        Text("AI Model")
                                            .font(.system(size: 15, weight: .semibold))
                                            .foregroundColor(.white)
                                    }
                                    .padding(.horizontal, 16)
                                    .padding(.top, 16)
                                    
                                    // Horizontal scroll of model cards
                                    ScrollView(.horizontal, showsIndicators: false) {
                                        HStack(spacing: 12) {
                                            ForEach(modelOptions) { opt in
                                                Button(action: {
                                                    viewModel.preferredModel = opt.name
                                                }) {
                                                    ZStack(alignment: .topTrailing) {
                                                        VStack(alignment: .leading, spacing: 6) {
                                                            Text(opt.name)
                                                                .font(.system(size: 13, weight: .bold))
                                                                .foregroundColor(.white)
                                                            
                                                            Text(opt.desc)
                                                                .font(.system(size: 11, weight: .medium))
                                                                .foregroundColor(viewModel.preferredModel == opt.name ? Color.appAccentTeal : Color.appSubtextGray)
                                                        }
                                                        .padding(.horizontal, 14)
                                                        .padding(.vertical, 12)
                                                        .frame(width: 136, height: 68, alignment: .leading)
                                                        .background(Color(hex: "#1A2230").opacity(viewModel.preferredModel == opt.name ? 1.0 : 0.4))
                                                        .cornerRadius(12)
                                                        .overlay(
                                                            RoundedRectangle(cornerRadius: 12)
                                                                .stroke(viewModel.preferredModel == opt.name ? Color.appAccentTeal : Color.white.opacity(0.05), lineWidth: viewModel.preferredModel == opt.name ? 1.5 : 1)
                                                        )
                                                        
                                                        // Selection indicator dot
                                                        if viewModel.preferredModel == opt.name {
                                                            Circle()
                                                                .fill(Color.appAccentTeal)
                                                                .frame(width: 6, height: 6)
                                                                .padding(8)
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        .padding(.horizontal, 16)
                                        .padding(.bottom, 16)
                                    }
                                }
                            }
                            .background(Color.appCardBackground)
                            .cornerRadius(24)
                            .overlay(
                                RoundedRectangle(cornerRadius: 24)
                                    .stroke(Color.white.opacity(0.04), lineWidth: 1)
                            )
                        }
                        .padding(.horizontal, 20)
                        
                        // 2. Appearance Section
                        VStack(alignment: .leading, spacing: 10) {
                            Text("APPEARANCE")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(Color.appSubtextGray)
                                .tracking(0.8)
                                .padding(.leading, 4)
                            
                            VStack(spacing: 0) {
                                // Dark Mode
                                Toggle(isOn: $viewModel.isDarkMode) {
                                    HStack(spacing: 12) {
                                        ZStack {
                                            RoundedRectangle(cornerRadius: 10)
                                                .fill(Color.white.opacity(0.03))
                                                .frame(width: 38, height: 38)
                                            
                                            Image(systemName: "moon.fill")
                                                .font(.system(size: 14))
                                                .foregroundColor(Color.appAccentTeal)
                                        }
                                        
                                        Text("Dark Mode")
                                            .font(.system(size: 15, weight: .semibold))
                                            .foregroundColor(.white)
                                    }
                                }
                                .tint(Color.appAccentTeal)
                                .padding(16)
                                
                                Divider()
                                    .background(Color.white.opacity(0.04))
                                    .padding(.horizontal, 16)
                                
                                // Compact Messages
                                Toggle(isOn: $viewModel.isCompactMessages) {
                                    HStack(spacing: 12) {
                                        ZStack {
                                            RoundedRectangle(cornerRadius: 10)
                                                .fill(Color.white.opacity(0.03))
                                                .frame(width: 38, height: 38)
                                            
                                            Image(systemName: "list.bullet")
                                                .font(.system(size: 14))
                                                .foregroundColor(Color.appAccentTeal)
                                        }
                                        
                                        Text("Compact Messages")
                                            .font(.system(size: 15, weight: .semibold))
                                            .foregroundColor(.white)
                                    }
                                }
                                .tint(Color.appAccentTeal)
                                .padding(16)
                                
                                Divider()
                                    .background(Color.white.opacity(0.04))
                                    .padding(.horizontal, 16)
                                
                                // Font Size Selector
                                HStack(spacing: 12) {
                                    ZStack {
                                        RoundedRectangle(cornerRadius: 10)
                                            .fill(Color.white.opacity(0.03))
                                            .frame(width: 38, height: 38)
                                        
                                        Image(systemName: "textformat.size")
                                            .font(.system(size: 14))
                                            .foregroundColor(Color.appAccentTeal)
                                    }
                                    
                                    Text("Font Size")
                                        .font(.system(size: 15, weight: .semibold))
                                        .foregroundColor(.white)
                                    
                                    Spacer()
                                    
                                    // Custom Segment Picker
                                    HStack(spacing: 0) {
                                        // Small A
                                        Button(action: { viewModel.fontSizeSelection = 0 }) {
                                            Text("A")
                                                .font(.system(size: 11, weight: .bold))
                                                .foregroundColor(viewModel.fontSizeSelection == 0 ? .white : Color.appSubtextGray)
                                                .frame(width: 32, height: 32)
                                                .background(viewModel.fontSizeSelection == 0 ? Color(hex: "#1A2230") : Color.clear)
                                                .cornerRadius(6)
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 6)
                                                        .stroke(viewModel.fontSizeSelection == 0 ? Color.white.opacity(0.1) : Color.clear, lineWidth: 1)
                                                )
                                        }
                                        
                                        // Medium A
                                        Button(action: { viewModel.fontSizeSelection = 1 }) {
                                            Text("A")
                                                .font(.system(size: 14, weight: .bold))
                                                .foregroundColor(viewModel.fontSizeSelection == 1 ? .white : Color.appSubtextGray)
                                                .frame(width: 32, height: 32)
                                                .background(viewModel.fontSizeSelection == 1 ? Color(hex: "#1A2230") : Color.clear)
                                                .cornerRadius(6)
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 6)
                                                        .stroke(viewModel.fontSizeSelection == 1 ? Color.white.opacity(0.1) : Color.clear, lineWidth: 1)
                                                )
                                        }
                                        
                                        // Large A
                                        Button(action: { viewModel.fontSizeSelection = 2 }) {
                                            Text("A")
                                                .font(.system(size: 18, weight: .bold))
                                                .foregroundColor(viewModel.fontSizeSelection == 2 ? .white : Color.appSubtextGray)
                                                .frame(width: 32, height: 32)
                                                .background(viewModel.fontSizeSelection == 2 ? Color(hex: "#1A2230") : Color.clear)
                                                .cornerRadius(6)
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 6)
                                                        .stroke(viewModel.fontSizeSelection == 2 ? Color.white.opacity(0.1) : Color.clear, lineWidth: 1)
                                                )
                                        }
                                    }
                                    .padding(4)
                                    .background(Color.black.opacity(0.3))
                                    .cornerRadius(8)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 8)
                                            .stroke(Color.white.opacity(0.04), lineWidth: 1)
                                    )
                                }
                                .padding(16)
                            }
                            .background(Color.appCardBackground)
                            .cornerRadius(24)
                            .overlay(
                                RoundedRectangle(cornerRadius: 24)
                                    .stroke(Color.white.opacity(0.04), lineWidth: 1)
                            )
                        }
                        .padding(.horizontal, 20)
                        
                        // 3. Notifications Section
                        VStack(alignment: .leading, spacing: 10) {
                            Text("NOTIFICATIONS")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(Color.appSubtextGray)
                                .tracking(0.8)
                                .padding(.leading, 4)
                            
                            VStack(spacing: 0) {
                                // Study Reminders
                                Toggle(isOn: $viewModel.isStudyReminders) {
                                    HStack(spacing: 12) {
                                        ZStack {
                                            RoundedRectangle(cornerRadius: 10)
                                                .fill(Color.white.opacity(0.03))
                                                .frame(width: 38, height: 38)
                                            
                                            Image(systemName: "bell.fill")
                                                .font(.system(size: 14))
                                                .foregroundColor(Color.appAccentTeal)
                                        }
                                        
                                        Text("Study Reminders")
                                            .font(.system(size: 15, weight: .semibold))
                                            .foregroundColor(.white)
                                    }
                                }
                                .tint(Color.appAccentTeal)
                                .padding(16)
                                
                                Divider()
                                    .background(Color.white.opacity(0.04))
                                    .padding(.horizontal, 16)
                                
                                // Streak Alerts
                                Toggle(isOn: $viewModel.isStreakAlerts) {
                                    HStack(spacing: 12) {
                                        ZStack {
                                            RoundedRectangle(cornerRadius: 10)
                                                .fill(Color.white.opacity(0.03))
                                                .frame(width: 38, height: 38)
                                            
                                            Image(systemName: "flame.fill")
                                                .font(.system(size: 14))
                                                .foregroundColor(Color.appAccentTeal)
                                        }
                                        
                                        Text("Streak Alerts")
                                            .font(.system(size: 15, weight: .semibold))
                                            .foregroundColor(.white)
                                    }
                                }
                                .tint(Color.appAccentTeal)
                                .padding(16)
                            }
                            .background(Color.appCardBackground)
                            .cornerRadius(24)
                            .overlay(
                                RoundedRectangle(cornerRadius: 24)
                                    .stroke(Color.white.opacity(0.04), lineWidth: 1)
                            )
                        }
                        .padding(.horizontal, 20)
                        
                        // 4. Data and Privacy Section
                        VStack(alignment: .leading, spacing: 10) {
                            Text("DATA AND PRIVACY")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(Color.appSubtextGray)
                                .tracking(0.8)
                                .padding(.leading, 4)
                            
                            VStack(spacing: 0) {
                                // Clear History Button
                                Button(action: {
                                    viewModel.clearHistory()
                                }) {
                                    HStack {
                                        Text("Clear History")
                                            .font(.system(size: 15, weight: .bold))
                                            .foregroundColor(.red)
                                        
                                        Spacer()
                                        
                                        Image(systemName: "trash")
                                            .font(.system(size: 14))
                                            .foregroundColor(.red)
                                    }
                                    .padding(16)
                                    .background(Color.appCardBackground)
                                    .cornerRadius(12)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 12)
                                            .stroke(Color.red.opacity(0.1), lineWidth: 1)
                                    )
                                }
                                .padding(.bottom, 12)
                                
                                // Delete Account Button
                                Button(action: {
                                    viewModel.deleteAccount()
                                }) {
                                    HStack {
                                        Text("Delete Account")
                                            .font(.system(size: 15, weight: .bold))
                                            .foregroundColor(.white)
                                        
                                        Spacer()
                                        
                                        Image(systemName: "exclamationmark.triangle.fill")
                                            .font(.system(size: 14))
                                            .foregroundColor(.white)
                                    }
                                    .padding(16)
                                    .background(Color.red)
                                    .cornerRadius(12)
                                    .shadow(color: Color.red.opacity(0.3), radius: 6)
                                }
                            }
                        }
                        .padding(.horizontal, 20)
                        .padding(.bottom, 32)
                        
                    }
                }
            }
        }
        .preferredColorScheme(.dark)
        .alert("Settings Saved", isPresented: $showingSaveAlert) {
            Button("OK", role: .cancel) { }
        } message: {
            Text("Your default preferences have been successfully updated.")
        }
    }
}

#Preview {
    SettingsView()
        .environmentObject(AppViewModel())
}
