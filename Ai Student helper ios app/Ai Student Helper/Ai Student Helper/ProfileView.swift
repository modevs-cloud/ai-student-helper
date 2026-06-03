//
//  ProfileView.swift
//  Ai Student Helper
//

import SwiftUI

struct ProfileView: View {
    @EnvironmentObject var viewModel: AppViewModel
    
    // Local state for editing name & email
    @State private var name = ""
    @State private var email = ""
    @State private var isEditing = false
    
    var body: some View {
        ZStack {
            Color.appBackground.ignoresSafeArea()
            
            VStack(spacing: 0) {
                // Header Row (Sign Out on Top Right)
                HStack {
                    Text("Profile")
                        .font(.system(size: 28, weight: .black))
                        .foregroundColor(.white)
                    
                    Spacer()
                    
                    Button(action: {
                        viewModel.isLoggedIn = false
                    }) {
                        HStack(spacing: 4) {
                            Image(systemName: "rectangle.portrait.and.arrow.right")
                                .font(.system(size: 14, weight: .bold))
                            Text("Sign Out")
                                .font(.system(size: 13, weight: .bold))
                        }
                        .foregroundColor(.red)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 8)
                        .background(Color.red.opacity(0.1))
                        .cornerRadius(12)
                    }
                }
                .padding(.horizontal, 20)
                .padding(.top, 20)
                .padding(.bottom, 20)
                
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(spacing: 28) {
                        
                        // 1. Avatar & User Information
                        VStack(spacing: 12) {
                            // Circular Initials Avatar
                            ZStack {
                                Circle()
                                    .fill(
                                        LinearGradient(
                                            colors: [Color(hex: "#0D7377"), Color(hex: "#084d50")],
                                            startPoint: .topLeading,
                                            endPoint: .bottomTrailing
                                        )
                                    )
                                    .frame(width: 96, height: 96)
                                    .shadow(color: Color.appAccentTeal.opacity(0.3), radius: 10)
                                    .overlay(
                                        Circle()
                                            .stroke(Color.white.opacity(0.1), lineWidth: 1.5)
                                    )
                                
                                let initials = "\(viewModel.firstName.prefix(1))\(viewModel.lastName.prefix(1))"
                                Text(initials.isEmpty ? "MH" : initials)
                                    .font(.system(size: 36, weight: .bold))
                                    .foregroundColor(.white)
                            }
                            
                            VStack(spacing: 4) {
                                let fullName = "\(viewModel.firstName) \(viewModel.lastName)".trimmingCharacters(in: .whitespaces)
                                Text(fullName.isEmpty ? "Student User" : fullName)
                                    .font(.system(size: 22, weight: .bold))
                                    .foregroundColor(.white)
                                
                                Text(viewModel.email.isEmpty ? "student@university.edu" : viewModel.email)
                                    .font(.system(size: 14))
                                    .foregroundColor(Color.appSubtextGray)
                            }
                            
                            // Signed in with Google Badge
                            HStack(spacing: 6) {
                                GoogleLogo(size: 14)
                                Text("Signed in with Google")
                                    .font(.system(size: 11, weight: .semibold))
                                    .foregroundColor(Color.white.opacity(0.9))
                            }
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(Color.white.opacity(0.04))
                            .cornerRadius(16)
                            .overlay(
                                RoundedRectangle(cornerRadius: 16)
                                    .stroke(Color.white.opacity(0.06), lineWidth: 1)
                            )
                        }
                        
                        // 2. Learning Statistics (2x2 Grid)
                        VStack(alignment: .leading, spacing: 12) {
                            Text("LEARNING STATISTICS")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(Color.appSubtextGray)
                                .tracking(0.8)
                                .padding(.leading, 4)
                            
                            LazyVGrid(columns: [GridItem(.flexible(), spacing: 14), GridItem(.flexible(), spacing: 14)], spacing: 14) {
                                // Stat 1
                                StatCard(number: "\(viewModel.totalChats)", label: "Total Chats")
                                // Stat 2
                                StatCard(number: "\(viewModel.questionsAsked)", label: "Questions Asked")
                                // Stat 3
                                StatCard(number: "\(viewModel.subjectsExplored.count)", label: "Subjects Explored")
                                // Stat 4
                                StatCard(number: "\(viewModel.dayStreak)", label: "Day Streak")
                            }
                        }
                        .padding(.horizontal, 20)
                        
                        // 3. Account Details Section
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Text("ACCOUNT DETAILS")
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundColor(Color.appSubtextGray)
                                    .tracking(0.8)
                                
                                Spacer()
                                
                                Button(action: {
                                    if isEditing {
                                        // Save edits to viewModel
                                        let parts = name.split(separator: " ", maxSplits: 1).map(String.init)
                                        if let first = parts.first {
                                            viewModel.firstName = first
                                        }
                                        if parts.count > 1 {
                                            viewModel.lastName = parts[1]
                                        } else {
                                            viewModel.lastName = ""
                                        }
                                        viewModel.email = email
                                    }
                                    isEditing.toggle()
                                }) {
                                    Text(isEditing ? "Done" : "Edit")
                                        .font(.system(size: 13, weight: .semibold))
                                        .foregroundColor(Color.appAccentTeal)
                                }
                            }
                            .padding(.horizontal, 4)
                            
                            VStack(spacing: 16) {
                                // Name Field
                                VStack(alignment: .leading, spacing: 6) {
                                    Text("Full Name")
                                        .font(.system(size: 12, weight: .medium))
                                        .foregroundColor(Color.appSubtextGray)
                                    
                                    if isEditing {
                                        TextField("", text: $name)
                                            .foregroundColor(.white)
                                            .font(.system(size: 14, weight: .medium))
                                            .padding(.horizontal, 16)
                                            .frame(height: 48)
                                            .background(Color(hex: "#1A2230"))
                                            .cornerRadius(12)
                                            .overlay(
                                                RoundedRectangle(cornerRadius: 12)
                                                    .stroke(Color.appAccentTeal, lineWidth: 1)
                                            )
                                    } else {
                                        let fullName = "\(viewModel.firstName) \(viewModel.lastName)".trimmingCharacters(in: .whitespaces)
                                        Text(fullName.isEmpty ? "Student User" : fullName)
                                            .foregroundColor(.white)
                                            .font(.system(size: 14, weight: .medium))
                                            .frame(maxWidth: .infinity, alignment: .leading)
                                            .padding(.horizontal, 16)
                                            .frame(height: 48)
                                            .background(Color.white.opacity(0.02))
                                            .cornerRadius(12)
                                    }
                                }
                                
                                // Email Field
                                VStack(alignment: .leading, spacing: 6) {
                                    Text("Email Address")
                                        .font(.system(size: 12, weight: .medium))
                                        .foregroundColor(Color.appSubtextGray)
                                    
                                    if isEditing {
                                        TextField("", text: $email)
                                            .foregroundColor(.white)
                                            .font(.system(size: 14, weight: .medium))
                                            .padding(.horizontal, 16)
                                            .frame(height: 48)
                                            .background(Color(hex: "#1A2230"))
                                            .cornerRadius(12)
                                            .overlay(
                                                RoundedRectangle(cornerRadius: 12)
                                                    .stroke(Color.appAccentTeal, lineWidth: 1)
                                            )
                                            .keyboardType(.emailAddress)
                                    } else {
                                        Text(viewModel.email.isEmpty ? "student@university.edu" : viewModel.email)
                                            .foregroundColor(.white)
                                            .font(.system(size: 14, weight: .medium))
                                            .frame(maxWidth: .infinity, alignment: .leading)
                                            .padding(.horizontal, 16)
                                            .frame(height: 48)
                                            .background(Color.white.opacity(0.02))
                                            .cornerRadius(12)
                                    }
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
                        .padding(.horizontal, 20)
                        .padding(.bottom, 32)
                        
                    }
                }
            }
        }
        .onAppear {
            name = "\(viewModel.firstName) \(viewModel.lastName)".trimmingCharacters(in: .whitespaces)
            email = viewModel.email
        }
        .preferredColorScheme(.dark)
    }
}

#Preview {
    ProfileView()
        .environmentObject(AppViewModel())
}
