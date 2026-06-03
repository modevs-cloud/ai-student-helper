//
//  MainTabView.swift
//  Ai Student Helper
//

import SwiftUI

struct MainTabView: View {
    @EnvironmentObject var viewModel: AppViewModel
    
    init() {
        // Fallback UIKit customization for earlier iOS versions
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = UIColor(Color.appCardBackground)
        
        // Active item colors
        appearance.stackedLayoutAppearance.selected.iconColor = UIColor(Color.appAccentTeal)
        appearance.stackedLayoutAppearance.selected.titleTextAttributes = [.foregroundColor: UIColor(Color.appAccentTeal)]
        
        // Inactive item colors
        appearance.stackedLayoutAppearance.normal.iconColor = UIColor(Color.appSubtextGray)
        appearance.stackedLayoutAppearance.normal.titleTextAttributes = [.foregroundColor: UIColor(Color.appSubtextGray)]
        
        UITabBar.appearance().standardAppearance = appearance
        UITabBar.appearance().scrollEdgeAppearance = appearance
    }
    
    var body: some View {
        TabView(selection: $viewModel.selectedTab) {
            ChatView()
                .tabItem {
                    Label("Chat", systemImage: "bubble.left.and.bubble.right.fill")
                }
                .tag(0)
                .toolbarBackground(Color.appCardBackground, for: .tabBar)
                .toolbarBackground(.visible, for: .tabBar)
            
            HistoryView()
                .tabItem {
                    Label("History", systemImage: "clock.fill")
                }
                .tag(1)
                .toolbarBackground(Color.appCardBackground, for: .tabBar)
                .toolbarBackground(.visible, for: .tabBar)
            
            ProfileView()
                .tabItem {
                    Label("Profile", systemImage: "person.fill")
                }
                .tag(2)
                .toolbarBackground(Color.appCardBackground, for: .tabBar)
                .toolbarBackground(.visible, for: .tabBar)
            
            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape.fill")
                }
                .tag(3)
                .toolbarBackground(Color.appCardBackground, for: .tabBar)
                .toolbarBackground(.visible, for: .tabBar)
            
            AboutView()
                .tabItem {
                    Label("About", systemImage: "info.circle.fill")
                }
                .tag(4)
                .toolbarBackground(Color.appCardBackground, for: .tabBar)
                .toolbarBackground(.visible, for: .tabBar)
        }
        .tint(Color.appAccentTeal)
        .preferredColorScheme(.dark)
    }
}

#Preview {
    MainTabView()
        .environmentObject(AppViewModel())
}
