//
//  SetupView.swift
//  Ai Student Helper
//

import SwiftUI

struct SetupView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var viewModel: AppViewModel
    @State private var firstName = ""
    @State private var lastName = ""
    @State private var primarySubject = ""
    @State private var navigateToWelcome = false
    
    let subjects = ["Math", "Science", "Computer Science", "History", "English", "Other"]
    
    var body: some View {
        ZStack {
            Color.authBackground.ignoresSafeArea()
            
            // Subtle Background Glow
            GeometryReader { geo in
                Circle()
                    .fill(Color.appAccentTeal.opacity(0.2))
                    .frame(width: geo.size.width * 0.75, height: geo.size.height * 0.5)
                    .blur(radius: 120)
                    .position(x: geo.size.width / 2, y: geo.size.height / 3)
            }
            .allowsHitTesting(false)
            
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    
                    // Main Card
                    VStack(spacing: 0) {
                        
                        // Header / Step Indicator
                        HStack(spacing: 0) {
                            // Back Button
                            Button(action: {
                                dismiss()
                            }) {
                                ZStack {
                                    Circle()
                                        .fill(Color.white.opacity(0.05))
                                        .frame(width: 40, height: 40)
                                        .overlay(
                                            Circle()
                                                .stroke(Color.white.opacity(0.05), lineWidth: 1)
                                        )
                                    
                                    Image(systemName: "chevron.left")
                                        .font(.system(size: 14, weight: .bold))
                                        .foregroundColor(Color.appSubtextGray)
                                }
                            }
                            
                            Spacer()
                            
                            // Step dashes
                            VStack(spacing: 4) {
                                Text("STEP 2 OF 2")
                                    .font(.system(size: 10, weight: .bold))
                                    .foregroundColor(Color.appSubtextGray)
                                    .tracking(1.0)
                                
                                HStack(spacing: 6) {
                                    Capsule()
                                        .fill(Color.white.opacity(0.1))
                                        .frame(width: 32, height: 4)
                                    
                                    Capsule()
                                        .fill(Color.appAccentTeal)
                                        .frame(width: 32, height: 4)
                                }
                            }
                            
                            Spacer()
                            
                            // Spacer to center the Step dash
                            Color.clear
                                .frame(width: 40, height: 40)
                        }
                        .padding(.bottom, 32)
                        
                        // Title Area
                        VStack(spacing: 8) {
                            Text("Tell us your name")
                                .font(.system(size: 30, weight: .heavy))
                                .foregroundColor(.white)
                                .tracking(-0.5)
                            
                            Text("Let's personalize your AI learning experience.")
                                .font(.system(size: 14))
                                .foregroundColor(Color.appSubtextGray)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal, 16)
                        }
                        .padding(.bottom, 32)
                        
                        // Form
                        VStack(spacing: 20) {
                            
                            // First Name
                            VStack(alignment: .leading, spacing: 8) {
                                Text("First Name")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(Color.white.opacity(0.8))
                                    .padding(.leading, 4)
                                
                                AuthTextField(
                                    placeholder: "e.g. Jordan",
                                    text: $firstName,
                                    iconName: ""
                                )
                            }
                            
                            // Last Name
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Last Name")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(Color.white.opacity(0.8))
                                    .padding(.leading, 4)
                                
                                AuthTextField(
                                    placeholder: "e.g. Smith",
                                    text: $lastName,
                                    iconName: ""
                                )
                            }
                            
                            // Subject Picker (Dropdown Menu)
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Select your primary subject")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(Color.white.opacity(0.8))
                                    .padding(.leading, 4)
                                
                                Menu {
                                    ForEach(subjects, id: \.self) { subject in
                                        Button(subject) {
                                            primarySubject = subject
                                        }
                                    }
                                } label: {
                                    HStack {
                                        Text(primarySubject.isEmpty ? "Choose a subject..." : primarySubject)
                                            .foregroundColor(primarySubject.isEmpty ? Color.appSubtextGray : .white)
                                            .font(.system(size: 14))
                                        
                                        Spacer()
                                        
                                        Image(systemName: "chevron.down")
                                            .font(.system(size: 14, weight: .bold))
                                            .foregroundColor(Color.appSubtextGray)
                                    }
                                    .padding(.horizontal, 16)
                                    .frame(height: 50)
                                    .background(Color(hex: "#1A2230"))
                                    .cornerRadius(12)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 12)
                                            .stroke(Color.white.opacity(0.05), lineWidth: 1)
                                    )
                                }
                            }
                            
                            // CTA Button
                            Button(action: {
                                viewModel.firstName = firstName
                                viewModel.lastName = lastName
                                viewModel.defaultSubject = primarySubject.isEmpty ? "Math" : primarySubject
                                navigateToWelcome = true
                            }) {
                                HStack(spacing: 8) {
                                    Text("Get Started")
                                        .font(.system(size: 16, weight: .bold))
                                    
                                    Image(systemName: "arrow.right")
                                        .font(.system(size: 16, weight: .bold))
                                }
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .frame(height: 54)
                                .background(Color.appAccentTeal)
                                .cornerRadius(16)
                                .shadow(color: Color.appAccentTeal.opacity(0.25), radius: 8, x: 0, y: 4)
                            }
                            .padding(.top, 24)
                        }
                        
                    }
                    .padding(28)
                    .background(Color.appCardBackground)
                    .cornerRadius(32)
                    .overlay(
                        RoundedRectangle(cornerRadius: 32)
                            .stroke(Color.white.opacity(0.05), lineWidth: 1)
                    )
                    .shadow(color: Color.black.opacity(0.5), radius: 24, x: 0, y: 12)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 40)
                    
                }
            }
        }
        .navigationBarBackButtonHidden(true)
        .navigationDestination(isPresented: $navigateToWelcome) {
            WelcomeView()
        }
        .onAppear {
            if firstName.isEmpty { firstName = viewModel.firstName }
            if lastName.isEmpty { lastName = viewModel.lastName }
            if primarySubject.isEmpty { primarySubject = viewModel.defaultSubject }
        }
    }
}

#Preview {
    SetupView()
        .environmentObject(AppViewModel())
}
