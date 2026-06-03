//
//  SignInView.swift
//  Ai Student Helper
//

import SwiftUI

struct SignInView: View {
    @Binding var isSignUp: Bool
    @EnvironmentObject var viewModel: AppViewModel
    @State private var email = ""
    @State private var password = ""

    
    var body: some View {
        ZStack {
            Color.authBackground.ignoresSafeArea()
            
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    
                    // 1. Header / Logo Section
                    VStack(spacing: 0) {
                        // Lightbulb Logo
                        ZStack {
                            RoundedRectangle(cornerRadius: 16)
                                .fill(
                                    LinearGradient(
                                        colors: [Color(hex: "#0D7377"), Color(hex: "#084d50")],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .frame(width: 64, height: 64)
                                .shadow(color: Color(hex: "#0D7377").opacity(0.2), radius: 8, x: 0, y: 4)
                            
                            Image(systemName: "lightbulb.fill")
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(width: 32, height: 32)
                                .foregroundColor(.white)
                        }
                        .padding(.bottom, 20)
                        
                        Text("AI Student Helper")
                            .font(.system(size: 24, weight: .bold))
                            .foregroundColor(.white)
                            .tracking(-0.5)
                            .padding(.bottom, 6)
                        
                        Text("Your personal study assistant")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(Color.appSubtextGray)
                    }
                    .padding(.top, 40)
                    .padding(.bottom, 32)
                    
                    // 2. Main Card
                    VStack(spacing: 0) {
                        
                        // Tabs (Sign In / Create Account)
                        HStack(spacing: 0) {
                            // Active Tab: Sign In
                            Text("Sign In")
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .frame(height: 38)
                                .background(Color(hex: "#1A2230"))
                                .cornerRadius(8)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(Color.white.opacity(0.05), lineWidth: 1)
                                )
                                .padding(4)
                            
                            // Inactive Tab: Create Account (Toggles State)
                            Button(action: {
                                withAnimation(.easeInOut(duration: 0.2)) {
                                    isSignUp = true
                                }
                            }) {
                                Text("Create Account")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(Color.appSubtextGray)
                                    .frame(maxWidth: .infinity)
                                    .frame(height: 38)
                            }
                        }
                        .background(Color.black.opacity(0.3))
                        .cornerRadius(12)
                        .padding(.bottom, 28)
                        
                        // Google Auth Button
                        Button(action: {
                            viewModel.email = "google.student@gmail.com"
                            viewModel.firstName = "Google"
                            viewModel.lastName = "Student"
                            viewModel.isLoggedIn = true
                        }) {
                            HStack(spacing: 12) {
                                GoogleLogo(size: 20)
                                Text("Continue with Google")
                                    .font(.system(size: 14, weight: .semibold))
                                    .foregroundColor(Color(hex: "#1f2937"))
                            }
                            .frame(maxWidth: .infinity)
                            .frame(height: 48)
                            .background(Color.white)
                            .cornerRadius(12)
                        }
                        .padding(.bottom, 28)
                        
                        // Divider
                        HStack(spacing: 16) {
                            Rectangle()
                                .fill(Color.white.opacity(0.1))
                                .frame(height: 1)
                            
                            Text("or sign in with email")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(Color.appSubtextGray)
                            
                            Rectangle()
                                .fill(Color.white.opacity(0.1))
                                .frame(height: 1)
                        }
                        .padding(.bottom, 24)
                        
                        // Form Fields
                        VStack(spacing: 16) {
                            AuthTextField(
                                placeholder: "Email address",
                                text: $email,
                                iconName: "envelope.fill",
                                keyboardType: .emailAddress
                            )
                            
                            AuthTextField(
                                placeholder: "Password",
                                text: $password,
                                iconName: "lock.fill",
                                isSecure: true
                            )
                        }
                        .padding(.bottom, 12)
                        
                        // Forgot Password Link
                        HStack {
                            Spacer()
                            Button(action: {
                                // Handle Forgot Password
                            }) {
                                Text("Forgot password?")
                                    .font(.system(size: 12, weight: .semibold))
                                    .foregroundColor(Color.appAccentTeal)
                            }
                        }
                        .padding(.bottom, 24)
                        
                        // Submit Button
                        Button(action: {
                            viewModel.email = email.isEmpty ? "student@university.edu" : email
                            viewModel.firstName = "Student"
                            viewModel.lastName = "User"
                            viewModel.isLoggedIn = true
                        }) {
                            Text("Sign In")
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .frame(height: 48)
                                .background(Color.appAccentTeal)
                                .cornerRadius(12)
                                .shadow(color: Color.appAccentTeal.opacity(0.25), radius: 8, x: 0, y: 4)
                        }
                        .padding(.bottom, 28)
                        
                        // Footer Link
                        HStack(spacing: 4) {
                            Text("Don't have an account?")
                                .font(.system(size: 12))
                                .foregroundColor(Color.appSubtextGray)
                            
                            Button(action: {
                                withAnimation(.easeInOut(duration: 0.2)) {
                                    isSignUp = true
                                }
                            }) {
                                Text("Create one for free")
                                    .font(.system(size: 12, weight: .semibold))
                                    .foregroundColor(Color.appAccentTeal)
                            }
                        }
                        
                    }
                    .padding(24)
                    .background(Color.appCardBackground)
                    .cornerRadius(28)
                    .overlay(
                        RoundedRectangle(cornerRadius: 28)
                            .stroke(Color.white.opacity(0.04), lineWidth: 1)
                    )
                    .shadow(color: Color.black.opacity(0.5), radius: 24, x: 0, y: 12)
                    .padding(.horizontal, 20)
                    
                    // 3. Trust Badges
                    HStack(alignment: .top, spacing: 16) {
                        // Badge 1
                        VStack(spacing: 10) {
                            ZStack {
                                Circle()
                                    .fill(Color.white.opacity(0.05))
                                    .frame(width: 40, height: 40)
                                    .overlay(
                                        Circle()
                                            .stroke(Color.white.opacity(0.05), lineWidth: 1)
                                    )
                                
                                Image(systemName: "checkmark.circle")
                                    .font(.system(size: 18))
                                    .foregroundColor(Color.appAccentTeal)
                            }
                            
                            Text("Free to use")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(Color.appSubtextGray)
                                .multilineTextAlignment(.center)
                                .tracking(0.5)
                        }
                        .frame(maxWidth: .infinity)
                        
                        // Badge 2
                        VStack(spacing: 10) {
                            ZStack {
                                Circle()
                                    .fill(Color.white.opacity(0.05))
                                    .frame(width: 40, height: 40)
                                    .overlay(
                                        Circle()
                                            .stroke(Color.white.opacity(0.05), lineWidth: 1)
                                    )
                                
                                Image(systemName: "bolt.fill")
                                    .font(.system(size: 18))
                                    .foregroundColor(Color.appAccentTeal)
                            }
                            
                            Text("Instant AI access")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(Color.appSubtextGray)
                                .multilineTextAlignment(.center)
                                .tracking(0.5)
                        }
                        .frame(maxWidth: .infinity)
                        
                        // Badge 3
                        VStack(spacing: 10) {
                            ZStack {
                                Circle()
                                    .fill(Color.white.opacity(0.05))
                                    .frame(width: 40, height: 40)
                                    .overlay(
                                        Circle()
                                            .stroke(Color.white.opacity(0.05), lineWidth: 1)
                                    )
                                
                                Image(systemName: "lock.fill")
                                    .font(.system(size: 18))
                                    .foregroundColor(Color.appAccentTeal)
                            }
                            
                            Text("Secure & private")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(Color.appSubtextGray)
                                .multilineTextAlignment(.center)
                                .tracking(0.5)
                        }
                        .frame(maxWidth: .infinity)
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 40)
                    .padding(.bottom, 40)
                    
                }
            }
        }

    }
}

#Preview {
    SignInView(isSignUp: .constant(false))
        .environmentObject(AppViewModel())
}
