//
//  SignUpView.swift
//  Ai Student Helper
//

import SwiftUI

struct SignUpView: View {
    @Binding var isSignUp: Bool
    @EnvironmentObject var viewModel: AppViewModel
    @State private var firstName = ""
    @State private var lastName = ""
    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var navigateToSetup = false
    
    var body: some View {
        ZStack {
            Color.authBackground.ignoresSafeArea()
            
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    
                    // 1. Header / Logo Section (Book Icon on Left, App Title on Right)
                    HStack(spacing: 12) {
                        ZStack {
                            RoundedRectangle(cornerRadius: 12)
                                .fill(
                                    LinearGradient(
                                        colors: [Color(hex: "#0D7377"), Color(hex: "#084d50")],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .frame(width: 44, height: 44)
                                .shadow(color: Color(hex: "#0D7377").opacity(0.15), radius: 6, x: 0, y: 3)
                            
                            Image(systemName: "book.fill")
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(width: 22, height: 22)
                                .foregroundColor(.white)
                        }
                        
                        Text("AI Student Helper")
                            .font(.system(size: 28, weight: .bold))
                            .foregroundColor(.white)
                            .tracking(-0.5)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 24)
                    .padding(.top, 40)
                    .padding(.bottom, 24)
                    
                    // 2. Main Card
                    VStack(spacing: 0) {
                        
                        // Tabs (Sign In / Create Account)
                        HStack(spacing: 0) {
                            // Inactive Tab: Sign In (Toggles State)
                            Button(action: {
                                withAnimation(.easeInOut(duration: 0.2)) {
                                    isSignUp = false
                                }
                            }) {
                                Text("Sign In")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(Color.appSubtextGray)
                                    .frame(maxWidth: .infinity)
                                    .frame(height: 38)
                            }
                            
                            // Active Tab: Create Account
                            Text("Create Account")
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
                        }
                        .background(Color.black.opacity(0.3))
                        .cornerRadius(12)
                        .padding(.bottom, 28)
                        
                        // Google Auth Button
                        Button(action: {
                            viewModel.email = "google.newstudent@gmail.com"
                            viewModel.firstName = "Google"
                            viewModel.lastName = "Student"
                            navigateToSetup = true
                        }) {
                            HStack(spacing: 12) {
                                GoogleLogo(size: 20)
                                Text("Sign up with Google")
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
                            
                            Text("OR CREATE WITH EMAIL")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(Color.appSubtextGray)
                                .tracking(0.5)
                            
                            Rectangle()
                                .fill(Color.white.opacity(0.1))
                                .frame(height: 1)
                        }
                        .padding(.bottom, 24)
                        
                        // Form Fields with Labels Above
                        VStack(spacing: 20) {
                            
                            // First Name & Last Name (Side by Side)
                            HStack(spacing: 16) {
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("First Name")
                                        .font(.system(size: 13, weight: .medium))
                                        .foregroundColor(Color.white.opacity(0.8))
                                    
                                    AuthTextField(
                                        placeholder: "Alex",
                                        text: $firstName,
                                        iconName: ""
                                    )
                                }
                                
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("Last Name")
                                        .font(.system(size: 13, weight: .medium))
                                        .foregroundColor(Color.white.opacity(0.8))
                                    
                                    AuthTextField(
                                        placeholder: "Chen",
                                        text: $lastName,
                                        iconName: ""
                                    )
                                }
                            }
                            
                            // Email Address
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Email Address")
                                    .font(.system(size: 13, weight: .medium))
                                    .foregroundColor(Color.white.opacity(0.8))
                                
                                AuthTextField(
                                    placeholder: "alex.chen@university.edu",
                                    text: $email,
                                    iconName: "",
                                    keyboardType: .emailAddress
                                )
                            }
                            
                            // Password
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Password")
                                    .font(.system(size: 13, weight: .medium))
                                    .foregroundColor(Color.white.opacity(0.8))
                                
                                AuthTextField(
                                    placeholder: "........",
                                    text: $password,
                                    iconName: "",
                                    isSecure: true
                                )
                            }
                            
                            // Confirm Password
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Confirm Password")
                                    .font(.system(size: 13, weight: .medium))
                                    .foregroundColor(Color.white.opacity(0.8))
                                
                                AuthTextField(
                                    placeholder: "........",
                                    text: $confirmPassword,
                                    iconName: "",
                                    isSecure: true
                                )
                            }
                        }
                        .padding(.bottom, 24)
                        
                        // Privacy Policy & TOS text
                        VStack(spacing: 4) {
                            Text("By creating an account, you agree to our")
                                .font(.system(size: 12))
                                .foregroundColor(Color.appSubtextGray)
                            
                            HStack(spacing: 4) {
                                Button(action: {
                                    // Open Terms of Service
                                }) {
                                    Text("Terms of Service")
                                        .font(.system(size: 12, weight: .medium))
                                        .foregroundColor(Color.appAccentTeal)
                                }
                                
                                Text("and")
                                    .font(.system(size: 12))
                                    .foregroundColor(Color.appSubtextGray)
                                
                                Button(action: {
                                    // Open Privacy Policy
                                }) {
                                    Text("Privacy Policy")
                                        .font(.system(size: 12, weight: .medium))
                                        .foregroundColor(Color.appAccentTeal)
                                }
                            }
                        }
                        .multilineTextAlignment(.center)
                        .padding(.bottom, 24)
                        
                        // Submit Button
                        Button(action: {
                            viewModel.email = email.isEmpty ? "newstudent@university.edu" : email
                            viewModel.firstName = firstName.isEmpty ? "New" : firstName
                            viewModel.lastName = lastName.isEmpty ? "Student" : lastName
                            navigateToSetup = true
                        }) {
                            Text("Create Account")
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .frame(height: 48)
                                .background(Color.appAccentTeal)
                                .cornerRadius(12)
                                .shadow(color: Color.appAccentTeal.opacity(0.25), radius: 8, x: 0, y: 4)
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
                    .padding(.bottom, 32)
                    
                    // 3. Footer Link (Navigate Back to Sign In)
                    HStack(spacing: 4) {
                        Text("Already have an account?")
                            .font(.system(size: 12))
                            .foregroundColor(Color.appSubtextGray)
                        
                        Button(action: {
                            withAnimation(.easeInOut(duration: 0.2)) {
                                isSignUp = false
                            }
                        }) {
                            Text("Sign in instead")
                                .font(.system(size: 12, weight: .semibold))
                                .foregroundColor(Color.appAccentTeal)
                        }
                    }
                    .padding(.bottom, 40)
                    
                }
            }
        }
        .navigationDestination(isPresented: $navigateToSetup) {
            SetupView()
        }
    }
}

#Preview {
    SignUpView(isSignUp: .constant(true))
        .environmentObject(AppViewModel())
}
