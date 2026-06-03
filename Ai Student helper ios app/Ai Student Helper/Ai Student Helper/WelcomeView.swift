//
//  WelcomeView.swift
//  Ai Student Helper
//

import SwiftUI

struct WelcomeView: View {
    @EnvironmentObject var viewModel: AppViewModel
    
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
            
            VStack(spacing: 0) {
                Spacer()
                
                // Centered Card Layout
                VStack(spacing: 0) {
                    // Teal Checkmark Icon
                    Image(systemName: "checkmark.circle.fill")
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(width: 72, height: 72)
                        .foregroundColor(Color.appAccentTeal)
                        .padding(.bottom, 28)
                        .shadow(color: Color.appAccentTeal.opacity(0.3), radius: 12)
                    
                    // Welcome Title
                    Text("Welcome, \(viewModel.firstName.isEmpty ? "Student" : viewModel.firstName)!")
                        .font(.system(size: 28, weight: .heavy))
                        .foregroundColor(.white)
                        .multilineTextAlignment(.center)
                        .tracking(-0.5)
                        .padding(.bottom, 12)
                    
                    // Tagline
                    Text("You are all set.")
                        .font(.system(size: 15))
                        .foregroundColor(Color.appSubtextGray)
                        .padding(.bottom, 36)
                    
                    // Go to Dashboard Button
                    Button(action: {
                        viewModel.isLoggedIn = true
                    }) {
                        HStack(spacing: 8) {
                            Text("Go to Dashboard")
                                .font(.system(size: 16, weight: .bold))
                            
                            Image(systemName: "arrow.right")
                                .font(.system(size: 16, weight: .bold))
                        }
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 52)
                        .background(Color.appAccentTeal)
                        .cornerRadius(14)
                        .shadow(color: Color.appAccentTeal.opacity(0.25), radius: 8, x: 0, y: 4)
                    }
                }
                .padding(32)
                .background(Color.appCardBackground)
                .cornerRadius(28)
                .overlay(
                    RoundedRectangle(cornerRadius: 28)
                        .stroke(Color.white.opacity(0.04), lineWidth: 1)
                )
                .shadow(color: Color.black.opacity(0.5), radius: 24, x: 0, y: 12)
                .padding(.horizontal, 24)
                
                Spacer()
            }
        }
        .navigationBarBackButtonHidden(true)
    }
}

#Preview {
    WelcomeView()
        .environmentObject(AppViewModel())
}
