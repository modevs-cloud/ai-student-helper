//
//  AboutView.swift
//  Ai Student Helper
//

import SwiftUI

struct GithubLogoShape: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        let w = rect.width / 24.0
        let h = rect.height / 24.0
        
        path.move(to: CGPoint(x: 12 * w, y: 2 * h))
        path.addCurve(to: CGPoint(x: 2 * w, y: 12 * h), control1: CGPoint(x: 6.477 * w, y: 2 * h), control2: CGPoint(x: 2 * w, y: 6.477 * h))
        path.addCurve(to: CGPoint(x: 8.839 * w, y: 21.489 * h), control1: CGPoint(x: 2 * w, y: 16.42 * h), control2: CGPoint(x: 4.865 * w, y: 20.166 * h))
        path.addCurve(to: CGPoint(x: 9.521 * w, y: 21.007 * h), control1: CGPoint(x: 9.339 * w, y: 21.581 * h), control2: CGPoint(x: 9.521 * w, y: 21.272 * h))
        path.addCurve(to: CGPoint(x: 9.508 * w, y: 19.307 * h), control1: CGPoint(x: 9.521 * w, y: 20.77 * h), control2: CGPoint(x: 9.513 * w, y: 20.141 * h))
        path.addCurve(to: CGPoint(x: 6.139 * w, y: 17.967 * h), control1: CGPoint(x: 6.726 * w, y: 19.91 * h), control2: CGPoint(x: 6.139 * w, y: 17.967 * h))
        path.addCurve(to: CGPoint(x: 5.029 * w, y: 16.503 * h), control1: CGPoint(x: 5.685 * w, y: 16.811 * h), control2: CGPoint(x: 5.029 * w, y: 16.503 * h))
        path.addCurve(to: CGPoint(x: 5.098 * w, y: 13.856 * h), control1: CGPoint(x: 4.926 * w, y: 16.25 * h), control2: CGPoint(x: 4.582 * w, y: 15.233 * h))
        path.addCurve(to: CGPoint(x: 7.848 * w, y: 14.881 * h), control1: CGPoint(x: 5.098 * w, y: 13.856 * h), control2: CGPoint(x: 5.938 * w, y: 13.587 * h))
        path.addCurve(to: CGPoint(x: 10.758 * w, y: 15.712 * h), control1: CGPoint(x: 8.74 * w, y: 16.175 * h), control2: CGPoint(x: 10.758 * w, y: 15.712 * h))
        path.addCurve(to: CGPoint(x: 11.394 * w, y: 14.376 * h), control1: CGPoint(x: 10.85 * w, y: 15.066 * h), control2: CGPoint(x: 11.11 * w, y: 14.626 * h))
        path.addCurve(to: CGPoint(x: 6.839 * w, y: 14.123 * h), control1: CGPoint(x: 9.174 * w, y: 14.123 * h), control2: CGPoint(x: 6.839 * w, y: 14.123 * h))
        path.addCurve(to: CGPoint(x: 2.284 * w, y: 9.18 * h), control1: CGPoint(x: 4.619 * w, y: 13.87 * h), control2: CGPoint(x: 2.284 * w, y: 13.01 * h))
        path.addCurve(to: CGPoint(x: 3.313 * w, y: 6.497 * h), control1: CGPoint(x: 2.284 * w, y: 8.089 * h), control2: CGPoint(x: 2.674 * w, y: 7.196 * h))
        path.addCurve(to: CGPoint(x: 3.411 * w, y: 3.85 * h), control1: CGPoint(x: 3.21 * w, y: 6.244 * h), control2: CGPoint(x: 2.867 * w, y: 5.227 * h))
        path.addCurve(to: CGPoint(x: 6.158 * w, y: 4.875 * h), control1: CGPoint(x: 3.411 * w, y: 3.85 * h), control2: CGPoint(x: 4.251 * w, y: 4.119 * h))
        path.addCurve(to: CGPoint(x: 8.662 * w, y: 5.212 * h), control1: CGPoint(x: 7.008 * w, y: 4.538 * h), control2: CGPoint(x: 7.863 * w, y: 5.101 * h))
        path.addCurve(to: CGPoint(x: 12 * w, y: 5.208 * h), control1: CGPoint(x: 9.72 * w, y: 5.093 * h), control2: CGPoint(x: 10.875 * w, y: 5.204 * h))
        path.addCurve(to: CGPoint(x: 15.338 * w, y: 5.212 * h), control1: CGPoint(x: 13.125 * w, y: 5.204 * h), control2: CGPoint(x: 14.28 * w, y: 5.093 * h))
        path.addCurve(to: CGPoint(x: 17.842 * w, y: 4.875 * h), control1: CGPoint(x: 16.137 * w, y: 5.101 * h), control2: CGPoint(x: 16.992 * w, y: 4.538 * h))
        path.addCurve(to: CGPoint(x: 20.589 * w, y: 3.85 * h), control1: CGPoint(x: 19.749 * w, y: 4.119 * h), control2: CGPoint(x: 20.589 * w, y: 3.85 * h))
        path.addCurve(to: CGPoint(x: 20.687 * w, y: 6.497 * h), control1: CGPoint(x: 21.133 * w, y: 5.227 * h), control2: CGPoint(x: 20.79 * w, y: 6.244 * h))
        path.addCurve(to: CGPoint(x: 21.716 * w, y: 9.18 * h), control1: CGPoint(x: 21.326 * w, y: 7.196 * h), control2: CGPoint(x: 21.716 * w, y: 8.089 * h))
        path.addCurve(to: CGPoint(x: 17.161 * w, y: 14.123 * h), control1: CGPoint(x: 21.716 * w, y: 13.01 * h), control2: CGPoint(x: 19.381 * w, y: 13.87 * h))
        path.addCurve(to: CGPoint(x: 12.596 * w, y: 14.376 * h), control1: CGPoint(x: 14.826 * w, y: 14.123 * h), control2: CGPoint(x: 12.596 * w, y: 14.123 * h))
        path.addCurve(to: CGPoint(x: 13.232 * w, y: 15.712 * h), control1: CGPoint(x: 12.88 * w, y: 14.626 * h), control2: CGPoint(x: 13.14 * w, y: 15.066 * h))
        path.addCurve(to: CGPoint(x: 14.242 * w, y: 14.881 * h), control1: CGPoint(x: 13.232 * w, y: 15.712 * h), control2: CGPoint(x: 15.25 * w, y: 16.175 * h))
        path.addCurve(to: CGPoint(x: 16.992 * w, y: 13.856 * h), control1: CGPoint(x: 16.002 * w, y: 14.881 * h), control2: CGPoint(x: 16.992 * w, y: 13.856 * h))
        path.addCurve(to: CGPoint(x: 17.061 * w, y: 16.503 * h), control1: CGPoint(x: 17.253 * w, y: 15.233 * h), control2: CGPoint(x: 16.91 * w, y: 16.25 * h))
        path.addCurve(to: CGPoint(x: 15.951 * w, y: 17.967 * h), control1: CGPoint(x: 17.061 * w, y: 16.503 * h), control2: CGPoint(x: 16.405 * w, y: 16.811 * h))
        path.addCurve(to: CGPoint(x: 12.582 * w, y: 19.307 * h), control1: CGPoint(x: 15.951 * w, y: 17.967 * h), control2: CGPoint(x: 15.364 * w, y: 19.91 * h))
        path.addCurve(to: CGPoint(x: 12.569 * w, y: 21.007 * h), control1: CGPoint(x: 12.582 * w, y: 19.307 * h), control2: CGPoint(x: 12.574 * w, y: 20.141 * h))
        path.addCurve(to: CGPoint(x: 13.251 * w, y: 21.489 * h), control1: CGPoint(x: 12.569 * w, y: 21.007 * h), control2: CGPoint(x: 12.751 * w, y: 21.272 * h))
        path.addCurve(to: CGPoint(x: 22 * w, y: 12 * h), control1: CGPoint(x: 13.251 * w, y: 21.489 * h), control2: CGPoint(x: 22 * w, y: 16.42 * h))
        path.addCurve(to: CGPoint(x: 12 * w, y: 2 * h), control1: CGPoint(x: 22 * w, y: 6.477 * h), control2: CGPoint(x: 17.523 * w, y: 2 * h))
        path.closeSubpath()
        
        return path
    }
}

struct GithubLogo: View {
    var size: CGFloat = 18
    var color: Color = .white
    
    var body: some View {
        GithubLogoShape()
            .fill(color)
            .frame(width: size, height: size)
    }
}

struct AboutView: View {
    var body: some View {
        ZStack {
            Color.appBackground.ignoresSafeArea()
            
            // Subtle Background Glow
            GeometryReader { geo in
                Circle()
                    .fill(Color.appAccentTeal.opacity(0.15))
                    .frame(width: 288, height: 288)
                    .blur(radius: 80)
                    .position(x: geo.size.width / 2, y: geo.size.height / 3)
            }
            .allowsHitTesting(false)
            
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    
                    // App Icon with Shadow
                    ZStack {
                        RoundedRectangle(cornerRadius: 28)
                            .fill(
                                LinearGradient(
                                    colors: [Color(hex: "#0D7377"), Color(hex: "#095457")],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 112, height: 112)
                            .shadow(color: Color(hex: "#0D7377").opacity(0.6), radius: 20, x: 0, y: 12)
                            .overlay(
                                RoundedRectangle(cornerRadius: 28)
                                    .stroke(Color.white.opacity(0.1), lineWidth: 1)
                            )
                        
                        Image(systemName: "sun.max")
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(width: 56, height: 56)
                            .foregroundColor(.white)
                    }
                    .padding(.top, 60)
                    .padding(.bottom, 24)
                    
                    // App Title
                    Text("AI Student Helper")
                        .font(.system(size: 30, weight: .heavy))
                        .foregroundColor(.white)
                        .tracking(-0.5)
                        .padding(.bottom, 16)
                    
                    // Version Badge
                    HStack(spacing: 8) {
                        Circle()
                            .fill(Color.appAccentTeal)
                            .frame(width: 8, height: 8)
                        
                        Text("VERSION 1.0.0 STABLE")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(Color(hex: "#d1d5db")) // zinc-300
                            .tracking(1.0)
                    }
                    .padding(.horizontal, 14)
                    .padding(.vertical, 6)
                    .background(Color(hex: "#18181b").opacity(0.8)) // zinc-900
                    .cornerRadius(20)
                    .overlay(
                        RoundedRectangle(cornerRadius: 20)
                            .stroke(Color(hex: "#27272a"), lineWidth: 1) // zinc-800
                    )
                    .padding(.bottom, 24)
                    
                    // Description
                    Text("Your intelligent companion for academic success. Organize notes, solve complex problems, and study smarter with the power of AI.")
                        .font(.system(size: 15))
                        .foregroundColor(Color.appSubtextGray)
                        .lineSpacing(6)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 40)
                        .padding(.bottom, 40)
                    
                    // Action Buttons
                    HStack(spacing: 12) {
                        // GitHub Button
                        Link(destination: URL(string: "https://github.com/modevs-cloud")!) {
                            HStack(spacing: 8) {
                                GithubLogo(size: 18, color: .white)
                                Text("GitHub")
                                    .font(.system(size: 14, weight: .medium))
                            }
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 48)
                            .background(
                                RoundedRectangle(cornerRadius: 16)
                                    .stroke(Color(hex: "#3f3f46"), lineWidth: 1) // zinc-700
                                    .background(Color(hex: "#18181b").opacity(0.5)) // zinc-900
                            )
                        }
                        
                        // Contact Us Button
                        Button(action: {
                            // Open Mail
                            if let url = URL(string: "mailto:support@modevs.cloud") {
                                UIApplication.shared.open(url)
                            }
                        }) {
                            HStack(spacing: 8) {
                                Image(systemName: "envelope.fill")
                                    .font(.system(size: 16))
                                Text("Contact Us")
                                    .font(.system(size: 14, weight: .medium))
                            }
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 48)
                            .background(Color.appAccentTeal)
                            .cornerRadius(16)
                            .shadow(color: Color.appAccentTeal.opacity(0.5), radius: 10, x: 0, y: 4)
                        }
                    }
                    .padding(.horizontal, 28)
                    .padding(.bottom, 48)
                    
                    Spacer()
                    
                    // Footer Text
                    VStack(spacing: 6) {
                        Text("Built by Mohammad Hussainkhail")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(Color(hex: "#71717a")) // zinc-500
                        
                        HStack(spacing: 6) {
                            Text("mo-dev")
                            Circle()
                                .fill(Color(hex: "#3f3f46"))
                                .frame(width: 4, height: 4)
                            Text("2026")
                            Circle()
                                .fill(Color(hex: "#3f3f46"))
                                .frame(width: 4, height: 4)
                            Text("First Project 🚀")
                        }
                        .font(.system(size: 11))
                        .foregroundColor(Color(hex: "#52525b")) // zinc-600
                    }
                    .padding(.bottom, 24)
                }
            }
        }
        .preferredColorScheme(.dark)
    }
}

#Preview {
    AboutView()
}
