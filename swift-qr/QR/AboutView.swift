import SwiftUI

struct AboutView: View {
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationView {
            Text("ha?")
                .toolbar {
                    Button ("Dismiss") {
                        dismiss()
                    }
                }
        }
    }
}

#Preview {
    AboutView()
}
