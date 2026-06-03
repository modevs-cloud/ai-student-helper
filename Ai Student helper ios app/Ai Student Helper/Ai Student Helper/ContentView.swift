//
//  ContentView.swift
//  Ai Student Helper
//
//  Created by Mohammad Hussainkhail on 6/2/26.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = AppViewModel()
    
    var body: some View {
        if viewModel.isLoggedIn {
            MainTabView()
                .environmentObject(viewModel)
        } else {
            NavigationStack {
                LandingView()
            }
            .environmentObject(viewModel)
        }
    }
}

struct AuthContainerView: View {
    @State var isSignUp: Bool
    
    var body: some View {
        if isSignUp {
            SignUpView(isSignUp: $isSignUp)
        } else {
            SignInView(isSignUp: $isSignUp)
        }
    }
}

#Preview {
    ContentView()
}
