//
//  Color+Theme.swift
//  Ai Student Helper
//
//  Created by Antigravity on 6/3/26.
//

import SwiftUI

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 1)
        }

        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
    
    static let appBackground = Color(hex: "#0a0a0a")
    static let appCardBackground = Color(hex: "#111720")
    static let appAccentTeal = Color(hex: "#0D7377")
    static let appSubtextGray = Color(hex: "#7a8a99")
    static let borderGray = Color(hex: "#1d2430")
    static let authBackground = Color(hex: "#0B0F19")
}

struct GoogleLogo: View {
    var size: CGFloat = 20
    
    var body: some View {
        GeometryReader { geometry in
            let s = min(geometry.size.width, geometry.size.height)
            let r = s / 2
            let c = CGPoint(x: geometry.size.width / 2, y: geometry.size.height / 2)
            let thickness = s * 0.24
            
            ZStack {
                // Red arc (Top)
                Path { path in
                    path.addArc(center: c, radius: r - thickness/2, startAngle: .degrees(-145), endAngle: .degrees(-45), clockwise: false)
                }
                .stroke(Color(hex: "#EA4335"), style: StrokeStyle(lineWidth: thickness, lineCap: .butt))
                
                // Yellow arc (Left)
                Path { path in
                    path.addArc(center: c, radius: r - thickness/2, startAngle: .degrees(135), endAngle: .degrees(-145), clockwise: false)
                }
                .stroke(Color(hex: "#FBBC05"), style: StrokeStyle(lineWidth: thickness, lineCap: .butt))
                
                // Green arc (Bottom)
                Path { path in
                    path.addArc(center: c, radius: r - thickness/2, startAngle: .degrees(45), endAngle: .degrees(135), clockwise: false)
                }
                .stroke(Color(hex: "#34A853"), style: StrokeStyle(lineWidth: thickness, lineCap: .butt))
                
                // Blue arc (Right)
                Path { path in
                    path.addArc(center: c, radius: r - thickness/2, startAngle: .degrees(-45), endAngle: .degrees(45), clockwise: false)
                }
                .stroke(Color(hex: "#4285F4"), style: StrokeStyle(lineWidth: thickness, lineCap: .butt))
                
                // Blue horizontal bar
                Path { path in
                    path.move(to: CGPoint(x: c.x, y: c.y))
                    path.addLine(to: CGPoint(x: c.x + r - thickness/2, y: c.y))
                }
                .stroke(Color(hex: "#4285F4"), style: StrokeStyle(lineWidth: thickness, lineCap: .square))
            }
        }
        .frame(width: size, height: size)
    }
}

extension View {
    func placeholder<Content: View>(
        when shouldShow: Bool,
        alignment: Alignment = .leading,
        @ViewBuilder placeholder: () -> Content) -> some View {

        ZStack(alignment: alignment) {
            placeholder().opacity(shouldShow ? 1 : 0)
            self
        }
    }
}

struct AuthTextField: View {
    let placeholder: String
    @Binding var text: String
    let iconName: String
    var isSecure: Bool = false
    @State private var isPasswordVisible: Bool = false
    var keyboardType: UIKeyboardType = .default
    
    @FocusState private var isFocused: Bool
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: iconName)
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(isFocused ? .appAccentTeal : .appSubtextGray)
                .frame(width: 20)
            
            if isSecure && !isPasswordVisible {
                SecureField("", text: $text)
                    .foregroundColor(.white)
                    .font(.system(size: 14))
                    .keyboardType(keyboardType)
                    .autocapitalization(.none)
                    .disableAutocorrection(true)
                    .placeholder(when: text.isEmpty) {
                        Text(placeholder)
                            .foregroundColor(Color.appSubtextGray)
                            .font(.system(size: 14))
                    }
            } else {
                TextField("", text: $text)
                    .foregroundColor(.white)
                    .font(.system(size: 14))
                    .keyboardType(keyboardType)
                    .autocapitalization(.none)
                    .disableAutocorrection(true)
                    .placeholder(when: text.isEmpty) {
                        Text(placeholder)
                            .foregroundColor(Color.appSubtextGray)
                            .font(.system(size: 14))
                    }
            }
            
            if isSecure {
                Button(action: {
                    isPasswordVisible.toggle()
                }) {
                    Image(systemName: isPasswordVisible ? "eye" : "eye.slash")
                        .font(.system(size: 16))
                        .foregroundColor(.appSubtextGray)
                }
            }
        }
        .padding(.horizontal, 16)
        .frame(height: 50)
        .background(Color(hex: "#1A2230"))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isFocused ? Color.appAccentTeal : Color.white.opacity(0.05), lineWidth: 1)
        )
        .focused($isFocused)
    }
}

struct StatCard: View {
    let number: String
    let label: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(number)
                .font(.system(size: 26, weight: .bold))
                .foregroundColor(.white)
            
            Text(label)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(Color.appSubtextGray)
                .lineLimit(1)
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.appCardBackground)
        .cornerRadius(20)
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(Color.white.opacity(0.04), lineWidth: 1)
        )
    }
}

