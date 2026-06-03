//
//  LandingView.swift
//  Ai Student Helper
//

import SwiftUI

struct LandingView: View {
    @EnvironmentObject var viewModel: AppViewModel
    @State private var navigateToSignUp = false
    @State private var navigateToSignIn = false
    
    var body: some View {
        ZStack {
            Color.appBackground.ignoresSafeArea()
            
            GeometryReader { geo in
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(spacing: 0) {
                        
                        // 1. Status Badge
                        HStack(spacing: 8) {
                            Circle()
                                .fill(Color.appAccentTeal)
                                .frame(width: 8, height: 8)
                            
                            Text("POWERED BY GROQ LLAMA 3 & GEMINI")
                                .font(.system(size: 11, weight: .bold, design: .default))
                                .foregroundColor(.white)
                                .tracking(0.5)
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(
                            RoundedRectangle(cornerRadius: 20)
                                .stroke(Color.borderGray, lineWidth: 1)
                                .background(Color.appCardBackground.opacity(0.4))
                        )
                        .padding(.top, 28)
                        
                        Spacer(minLength: 40)
                        
                        // 2. Logo Icon
                        ZStack {
                            RoundedRectangle(cornerRadius: 24)
                                .fill(Color.appAccentTeal)
                                .frame(width: 100, height: 100)
                            
                            Image(systemName: "graduationcap.fill")
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(width: 50, height: 50)
                                .foregroundColor(.white)
                        }
                        .padding(.bottom, 24)
                        
                        // 3. Title & Tagline
                        Text("AI Student Helper")
                            .font(.system(size: 32, weight: .bold, design: .default))
                            .foregroundColor(.white)
                            .padding(.bottom, 8)
                        
                        Text("Your AI-powered study companion")
                            .font(.system(size: 16, weight: .regular))
                            .foregroundColor(Color.appSubtextGray)
                            .padding(.bottom, 48)
                        
                        Spacer(minLength: 40)
                        
                        // 4. Action Buttons
                        VStack(spacing: 16) {
                            // Google Sign In Button
                            Button(action: {
                                viewModel.email = "google.student@gmail.com"
                                viewModel.firstName = "Google"
                                viewModel.lastName = "Student"
                                viewModel.isLoggedIn = true
                            }) {
                                HStack(spacing: 12) {
                                    GoogleLogo(size: 18)
                                    Text("Continue with Google")
                                        .font(.system(size: 16, weight: .semibold))
                                        .foregroundColor(.white)
                                }
                                .frame(maxWidth: .infinity)
                                .frame(height: 56)
                                .background(
                                    RoundedRectangle(cornerRadius: 14)
                                        .stroke(Color.borderGray, lineWidth: 1)
                                        .background(Color.appCardBackground.opacity(0.2))
                                )
                            }
                            
                            // Create Account Button
                            Button(action: {
                                navigateToSignUp = true
                            }) {
                                Text("Create Account")
                                    .font(.system(size: 16, weight: .semibold))
                                    .foregroundColor(.white)
                                    .frame(maxWidth: .infinity)
                                    .frame(height: 56)
                                    .background(Color.appAccentTeal)
                                    .cornerRadius(14)
                            }
                            
                            // Sign In Button
                            Button(action: {
                                navigateToSignIn = true
                            }) {
                                Text("Sign In")
                                    .font(.system(size: 16, weight: .semibold))
                                    .foregroundColor(.white)
                                    .frame(maxWidth: .infinity)
                                    .frame(height: 56)
                                    .background(
                                        RoundedRectangle(cornerRadius: 14)
                                            .stroke(Color.borderGray, lineWidth: 1)
                                    )
                            }
                        }
                        .padding(.horizontal, 8)
                        .padding(.bottom, 48)
                        
                        Spacer(minLength: 20)
                        
                        // 5. Trust Badges
                        VStack(spacing: 12) {
                            HStack(spacing: 6) {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 12, weight: .bold))
                                    .foregroundColor(Color.appAccentTeal)
                                Text("No credit card required")
                                    .font(.system(size: 13, weight: .medium))
                                    .foregroundColor(Color.appSubtextGray)
                            }
                            
                            HStack(spacing: 20) {
                                HStack(spacing: 6) {
                                    Image(systemName: "checkmark")
                                        .font(.system(size: 12, weight: .bold))
                                        .foregroundColor(Color.appAccentTeal)
                                    Text("Instant AI responses")
                                        .font(.system(size: 13, weight: .medium))
                                        .foregroundColor(Color.appSubtextGray)
                                }
                                
                                HStack(spacing: 6) {
                                    Image(systemName: "checkmark")
                                        .font(.system(size: 12, weight: .bold))
                                        .foregroundColor(Color.appAccentTeal)
                                    Text("Chat history saved")
                                        .font(.system(size: 13, weight: .medium))
                                        .foregroundColor(Color.appSubtextGray)
                                }
                            }
                        }
                        .padding(.bottom, 24)
                        
                    }
                    .frame(minHeight: geo.size.height - geo.safeAreaInsets.top - geo.safeAreaInsets.bottom)
                    .padding(.horizontal, 24)
                }
            }
        }
        .navigationDestination(isPresented: $navigateToSignUp) {
            AuthContainerView(isSignUp: true)
        }
        .navigationDestination(isPresented: $navigateToSignIn) {
            AuthContainerView(isSignUp: false)
        }
    }
}

struct LandingView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationStack {
            LandingView()
                .environmentObject(AppViewModel())
        }
    }
}
