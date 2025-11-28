import SwiftUI
import MapKit

struct ContentView: View {
    @StateObject private var floatsViewModel = FloatsViewModel()

    var body: some View {
        TabView {
            ChatView(viewModel: floatsViewModel)
                .tabItem {
                    Image(systemName: "bubble.left.and.bubble.right.fill")
                    Text("Chat")
                }
            MapsView(viewModel: floatsViewModel)
                .tabItem {
                    Image(systemName: "map.fill")
                    Text("Maps")
                }
            FloatsView(viewModel: floatsViewModel)
                .tabItem {
                    Image(systemName: "waveform.path.ecg.rectangle")
                    Text("Floats")
                }
            AnalysisView(viewModel: floatsViewModel)
                .tabItem {
                    Image(systemName: "chart.xyaxis.line")
                    Text("Analysis")
                }
        }
        .tint(.cyan)
        .preferredColorScheme(.dark)
    }
}

// MARK: - Chat View

struct ChatView: View {
    @ObservedObject var viewModel: FloatsViewModel
    @State private var showMenu = false
    @State private var messageText = ""
    @State private var messages: [ChatMessage] = [
        ChatMessage(text: "Hello! I'm FloatChat. Ask me about ocean data, floats, or trends.", isMe: false)
    ]
    
    struct ChatMessage: Identifiable {
        let id = UUID()
        let text: String
        let isMe: Bool
        let date = Date()
    }
    
    var body: some View {
        ZStack {
            LinearGradient(gradient: Gradient(colors: [Color("BackgroundBlue"), Color("BackgroundBlueDark")]), startPoint: .top, endPoint: .bottom)
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                // Top Bar
                HStack {
                    Button(action: {
                        withAnimation(.easeInOut(duration: 0.3)) {
                            showMenu.toggle()
                        }
                    }) {
                        Image(systemName: "line.3.horizontal")
                            .foregroundColor(.white)
                            .font(.title2)
                    }
                    .padding(.horizontal)
                    
                    Spacer()
                    Text("Float Chat")
                        .font(.headline)
                        .foregroundColor(.white)
                    Spacer()
                    if viewModel.isLoadingChat {
                        ProgressView()
                            .tint(.white)
                            .padding(.trailing)
                    } else {
                        Spacer().frame(width: 40)
                    }
                }
                .padding(.vertical, 12)
                .background(Color("BackgroundBlue").opacity(0.9))
                .overlay(Rectangle().frame(height: 1).foregroundColor(.white.opacity(0.08)), alignment: .bottom)
                
                // Chat Messages ScrollView
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 20) {
                            ForEach(messages) { msg in
                                ChatBubble(message: msg.text, isMe: msg.isMe, time: msg.date.formatted(date: .omitted, time: .shortened))
                                    .id(msg.id)
                            }
                        }
                        .padding(.horizontal)
                        .padding(.top, 8)
                    }
                    .onChange(of: messages.count) { _ in
                        if let last = messages.last {
                            withAnimation {
                                proxy.scrollTo(last.id, anchor: .bottom)
                            }
                        }
                    }
                }
                .background(Color.clear)
                
                // Message Input
                HStack {
                    RoundedRectangle(cornerRadius: 20)
                        .fill(Color.white.opacity(0.15))
                        .overlay(
                            TextField("Message", text: $messageText)
                                .padding(.horizontal)
                                .foregroundColor(.white)
                                .accentColor(.white)
                                .onSubmit { sendMessage() }
                        )
                        .frame(height: 44)
                    Button(action: sendMessage) {
                        Image(systemName: "paperplane.fill")
                            .foregroundColor(.white)
                            .padding(12)
                            .background(RoundedRectangle(cornerRadius: 20).fill(Color.white.opacity(0.15)))
                    }
                    .disabled(messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
                .padding([.horizontal, .bottom])
            }
            
            // Side menu overlay
            GeometryReader { geometry in
                if showMenu {
                    Color.black.opacity(0.2)
                        .ignoresSafeArea()
                        .frame(width: geometry.size.width, height: geometry.size.height)
                        .zIndex(1)
                        .onTapGesture {
                            withAnimation(.easeInOut(duration: 0.3)) {
                                showMenu = false
                            }
                        }
                    
                    HStack(alignment: .top, spacing: 0) {
                        ChatHistoryMenu(width: 300)
                            .offset(x: showMenu ? 0 : -300)
                            .zIndex(2)
                        Spacer()
                    }
                    .frame(width: geometry.size.width, height: geometry.size.height)
                    .animation(.easeInOut(duration: 0.3), value: showMenu)
                }
            }
            .zIndex(10)
        }
        .onChange(of: viewModel.chatResponse?.message) { newResponse in
            if let response = newResponse {
                messages.append(ChatMessage(text: response, isMe: false))
            }
        }
    }
    
    private func sendMessage() {
        guard !messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        let text = messageText
        messageText = ""
        messages.append(ChatMessage(text: text, isMe: true))
        
        Task {
            await viewModel.sendChatQuery(text)
        }
    }
}

struct ChatBubble: View {
    let message: String
    let isMe: Bool
    let time: String
    
    var body: some View {
        HStack {
            if isMe { Spacer() }
            VStack(alignment: isMe ? .trailing : .leading, spacing: 2) {
                Text(message)
                    .foregroundColor(.white)
                    .padding(12)
                    .background(
                        RoundedRectangle(cornerRadius: 18)
                            .fill(isMe ? Color.blue : Color.white.opacity(0.13))
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 18)
                            .stroke(Color.white.opacity(isMe ? 0 : 0.25), lineWidth: 1)
                    )
                Text(time)
                    .font(.caption2)
                    .foregroundColor(.white.opacity(0.7))
                    .padding(isMe ? .trailing : .leading, 8)
                    .padding(.bottom, 2)
            }
            .frame(maxWidth: 260, alignment: isMe ? .trailing : .leading)
            if !isMe { Spacer() }
        }
    }
}

// Chat Side Menu
struct ChatHistoryMenu: View {
    var width: CGFloat
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Center the label:
            HStack {
                Spacer()
                Text("Chat History")
                    .font(.title2).bold()
                    .foregroundColor(.white)
                Spacer()
            }
            .padding(.top, 56)
            .padding(.bottom, 16)
            
            Divider().background(Color.white.opacity(0.1))
            
            ScrollView {
                VStack(spacing: 0) {
                    ChatHistoryRow(title: "Current Chat", detail: "Active Session", date: "Now")
                }
            }
            
            Button(action: {}) {
                Text("New Chat")
                    .foregroundColor(.white)
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(RoundedRectangle(cornerRadius: 16).fill(Color.white.opacity(0.18)))
            }
            .padding(.horizontal)
            .padding(.top, 16)
            .padding(.bottom, 100)
        }
        .frame(width: width)
        .background(Color("ChatHistoryBlue"))
        .ignoresSafeArea(.all, edges: .vertical)
    }
}

struct ChatHistoryRow: View {
    let title: String
    let detail: String
    let date: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title).font(.headline).foregroundColor(.white)
            Text(detail).font(.subheadline).foregroundColor(.white.opacity(0.8)).lineLimit(1)
            Text(date).font(.caption2).foregroundColor(.white.opacity(0.6))
        }
        .padding(.vertical, 8)
        .padding(.horizontal)
    }
}

// MARK: - Maps View

struct MapsView: View {
    @ObservedObject var viewModel: FloatsViewModel
    @State private var searchText = ""
    @State private var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 15, longitude: 70),
        span: MKCoordinateSpan(latitudeDelta: 30, longitudeDelta: 30)
    )
    
    // New Controls
    @State private var selectedMode = 0 // 0: Radius, 1: Indian Ocean, 2: All
    @State private var showTrajectories = false
    @State private var radius: Double = 500
    @State private var selectedFloat: FloatSummary?
    @State private var refreshTask: Task<Void, Never>?

    var body: some View {
        ZStack {
            LinearGradient(gradient: Gradient(colors: [Color("BackgroundBlue"), Color("BackgroundBlueDark")]), startPoint: .top, endPoint: .bottom)
                .ignoresSafeArea()
            
            // Map Layer
            Map(coordinateRegion: $region, annotationItems: viewModel.floats) { float in
                MapAnnotation(coordinate: CLLocationCoordinate2D(latitude: float.latitude, longitude: float.longitude)) {
                    VStack(spacing: 4) {
                        Image(systemName: "mappin.circle.fill")
                            .foregroundColor(.blue)
                            .font(.title2)
                            .onTapGesture {
                                selectedFloat = float
                                Task { await viewModel.fetchFloatDetails(id: float.floatId) }
                            }
                        if selectedFloat?.id == float.id {
                            Text(float.floatId)
                                .font(.caption2)
                                .foregroundColor(.white)
                                .padding(4)
                                .background(Color.black.opacity(0.6))
                                .clipShape(RoundedRectangle(cornerRadius: 6))
                        }
                    }
                }
            }
            .ignoresSafeArea()
            .onTapGesture {
                selectedFloat = nil
            }
            
            // Controls Overlay
            VStack(spacing: 0) {
                // Top Control Bar
                VStack(spacing: 8) {
                    HStack(spacing: 8) {
                        // Mode Picker
                        Picker("Mode", selection: $selectedMode) {
                            Text("Radius").tag(0)
                            Text("Indian Ocean").tag(1)
                            Text("All").tag(2)
                        }
                        .pickerStyle(.segmented)
                        .background(Material.ultraThinMaterial)
                        .cornerRadius(8)
                        
                        // Trajectory Toggle
                        Button(action: { showTrajectories.toggle() }) {
                            Image(systemName: showTrajectories ? "arrow.triangle.turn.up.right.circle.fill" : "arrow.triangle.turn.up.right.circle")
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(width: 20, height: 20)
                                .foregroundColor(showTrajectories ? .blue : .white)
                                .padding(6)
                                .background(Material.ultraThinMaterial)
                                .clipShape(Circle())
                        }
                        .frame(height: 32)
                    }
                    
                    // Radius Slider (only in Radius mode)
                    if selectedMode == 0 {
                        HStack {
                            Text("Radius: \(Int(radius)) km")
                                .font(.caption2)
                                .foregroundColor(.white)
                                .padding(4)
                                .background(Color.black.opacity(0.4))
                                .cornerRadius(4)
                            Slider(value: $radius, in: 100...5000, step: 100)
                                .tint(.white)
                        }
                        .padding(8)
                        .background(Material.ultraThinMaterial)
                        .cornerRadius(8)
                    }
                }
                .padding(.horizontal)
                .padding(.top, 60)
                
                Spacer()
                
                // Refresh Button (Bottom Right)
                HStack {
                    Spacer()
                    Button(action: refreshData) {
                        if viewModel.isLoadingNearby {
                            ProgressView().tint(.white)
                                .padding()
                                .background(Material.ultraThinMaterial)
                                .clipShape(Circle())
                        } else {
                            Image(systemName: "arrow.clockwise")
                                .font(.title2)
                                .foregroundColor(.white)
                                .padding()
                                .background(Material.ultraThinMaterial)
                                .clipShape(Circle())
                        }
                    }
                    .padding(.trailing, 20)
                    .padding(.bottom, 30)
                }
            }
            
            // Float Details Popup
            if let float = selectedFloat {
                VStack {
                    Spacer()
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text("Float \(float.floatId)")
                                .font(.title3).bold()
                                .foregroundColor(.white)
                            Spacer()
                            Button(action: { selectedFloat = nil }) {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundColor(.white.opacity(0.7))
                                    .font(.title2)
                            }
                        }
                        
                        if viewModel.isLoadingDetails {
                            HStack {
                                Spacer()
                                ProgressView().tint(.white)
                                Spacer()
                            }
                            .padding()
                        } else if let details = viewModel.floatDetails, details.floatId == float.floatId {
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Label(details.profile.datetime ?? "Unknown", systemImage: "clock")
                                    Spacer()
                                    Label("\(String(format: "%.4f", details.profile.latitude)), \(String(format: "%.4f", details.profile.longitude))", systemImage: "location")
                                }
                                .font(.caption)
                                .foregroundColor(.white.opacity(0.8))
                                
                                Divider().background(Color.white.opacity(0.2))
                                
                                if let measurement = details.measurements.first {
                                    HStack(spacing: 20) {
                                        MetricView(label: "Temp", value: String(format: "%.1f°C", measurement.temperature ?? 0), icon: "thermometer")
                                        MetricView(label: "Pressure", value: String(format: "%.0f dbar", measurement.pressure ?? 0), icon: "gauge")
                                        MetricView(label: "Salinity", value: String(format: "%.1f PSU", measurement.salinity ?? 0), icon: "drop")
                                    }
                                } else {
                                    Text("No measurement data available")
                                        .font(.caption)
                                        .foregroundColor(.white.opacity(0.6))
                                }
                            }
                        } else {
                            Text("Failed to load details")
                                .font(.caption)
                                .foregroundColor(.red.opacity(0.8))
                        }
                    }
                    .padding()
                    .background(Material.regularMaterial)
                    .cornerRadius(20)
                    .padding()
                    .shadow(radius: 10)
                }
                .transition(.move(edge: .bottom))
                .zIndex(100)
            }
        }
        .onChange(of: selectedMode) { _ in refreshData() }
        .onChange(of: showTrajectories) { show in
            if show {
                Task {
                    await viewModel.fetchTrajectories(lat: region.center.latitude, lon: region.center.longitude, radius: radius)
                }
            }
        }
        // Reactive Map Updates
        .onChange(of: region.center.latitude) { _ in delayedRefresh() }
        .onChange(of: region.center.longitude) { _ in delayedRefresh() }
        .onChange(of: region.span.latitudeDelta) { _ in delayedRefresh() }
        .onChange(of: radius) { _ in delayedRefresh() }
    }
    
    private func delayedRefresh() {
        guard selectedMode == 0 else { return } // Only refresh in Radius mode
        refreshTask?.cancel()
        refreshTask = Task {
            try? await Task.sleep(nanoseconds: 600_000_000) // 0.6s debounce
            if !Task.isCancelled {
                refreshData()
            }
        }
    }
    
    private func refreshData() {
        Task {
            let center = region.center
            switch selectedMode {
            case 0:
                await viewModel.fetchNearby(lat: center.latitude, lon: center.longitude, radius: radius)
            case 1:
                await viewModel.fetchIndianOceanFloats()
            case 2:
                await viewModel.fetchAllFloats()
            default: break
            }
        }
    }
}

struct MetricView: View {
    let label: String
    let value: String
    let icon: String
    
    var body: some View {
        VStack(spacing: 4) {
            Image(systemName: icon)
                .font(.caption)
                .foregroundColor(.blue)
            Text(value)
                .font(.subheadline).bold()
                .foregroundColor(.white)
            Text(label)
                .font(.caption2)
                .foregroundColor(.white.opacity(0.6))
        }
        .frame(maxWidth: .infinity)
    }
}

struct FilterChip: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.subheadline)
                .fontWeight(isSelected ? .bold : .regular)
                .foregroundColor(isSelected ? .black : .white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(
                    Capsule()
                        .fill(isSelected ? Color.white : Color.white.opacity(0.15))
                )
        }
    }
}

// MARK: - Floats View

struct FloatsView: View {
    @ObservedObject var viewModel: FloatsViewModel
    @State private var floatID = ""
    @State private var latText = "15.0"
    @State private var lonText = "70.0"
    @State private var radiusText = "500"
    @State private var hasLoaded = false
    
    var body: some View {
        ZStack {
            LinearGradient(gradient: Gradient(colors: [Color("BackgroundBlue"), Color("BackgroundBlueDark")]), startPoint: .top, endPoint: .bottom)
                .ignoresSafeArea()
            ScrollView {
                VStack {
                    Text("Float Tracker")
                        .font(.title2).bold()
                        .foregroundColor(.white)
                        .padding(.top, 56)
                    Text("Ocean Float Monitoring")
                        .font(.subheadline)
                        .foregroundColor(.white.opacity(0.79))
                        .padding(.bottom, 16)
                    FloatDetailsSection
                    NearbyFloatsSection
                    Spacer()
                }
            }
        }
        .onAppear {
            guard !hasLoaded else { return }
            hasLoaded = true
            Task {
                await fetchNearby()
            }
        }
    }

    private var NearbyFloatsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                CoordinateField(title: "Lat", text: $latText)
                CoordinateField(title: "Lon", text: $lonText)
                CoordinateField(title: "Radius (km)", text: $radiusText)
            }
            .padding(.horizontal)

            Button {
                Task { await fetchNearby() }
            } label: {
                HStack {
                    if viewModel.isLoadingNearby {
                        ProgressView()
                            .tint(.white)
                            .padding(.trailing, 8)
                    }
                    Text("Fetch Floats Near Location")
                        .fontWeight(.semibold)
                    Spacer()
                    Image(systemName: "arrow.clockwise")
                }
                .foregroundColor(.white)
                .padding()
                .background(RoundedRectangle(cornerRadius: 18).fill(Color.white.opacity(0.18)))
            }
            .padding(.horizontal)

            if let error = viewModel.errorMessage {
                Text(error)
                    .foregroundColor(.red.opacity(0.9))
                    .font(.footnote)
                    .padding(.horizontal)
            }

            if viewModel.floats.isEmpty && !viewModel.isLoadingNearby {
                RoundedRectangle(cornerRadius: 22)
                    .stroke(Color.white.opacity(0.23), lineWidth: 1)
                    .background(RoundedRectangle(cornerRadius: 22).fill(Color.white.opacity(0.11)))
                    .overlay(
                        VStack(spacing: 8) {
                            Image(systemName: "waveform.path.ecg.rectangle")
                                .font(.largeTitle)
                                .foregroundColor(.white.opacity(0.7))
                            Text("No floats loaded yet")
                                .foregroundColor(.white.opacity(0.7))
                            Text("Adjust the location and tap fetch")
                                .font(.caption)
                                .foregroundColor(.white.opacity(0.5))
                        }
                    )
                    .frame(height: 160)
                    .padding(.horizontal)
            } else {
                VStack(alignment: .leading, spacing: 12) {
                    ForEach(viewModel.floats) { float in
                        FloatRow(float: float) {
                            floatID = float.floatId
                            Task { await viewModel.fetchFloatDetails(id: float.floatId) }
                        }
                    }
                }
                .padding(.horizontal)
            }
        }
    }

    private var FloatDetailsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Float ID:")
                    .foregroundColor(.white.opacity(0.8))
                    .font(.subheadline)
                RoundedRectangle(cornerRadius: 14)
                    .fill(Color.white.opacity(0.16))
                    .overlay(
                        TextField("Enter Float ID (e.g., 5904468)", text: $floatID)
                            .padding(.horizontal, 10)
                            .foregroundColor(.white)
                            .accentColor(.white)
                    )
                    .frame(height: 40)
                Button {
                    Task { await viewModel.fetchFloatDetails(id: floatID) }
                } label: {
                    if viewModel.isLoadingDetails {
                        ProgressView().tint(.white).padding(10)
                    } else {
                        Image(systemName: "magnifyingglass")
                            .foregroundColor(.white)
                            .padding(10)
                    }
                }
                .background(RoundedRectangle(cornerRadius: 12).fill(Color.white.opacity(0.17)))
            }
            .padding(.horizontal)

            if let details = viewModel.floatDetails {
                FloatDetailsCard(details: details, viewModel: viewModel)
                    .padding(.horizontal)
            }
        }
    }

    private func fetchNearby() async {
        let lat = Double(latText) ?? 15
        let lon = Double(lonText) ?? 70
        let radius = Double(radiusText) ?? 500
        await viewModel.fetchNearby(lat: lat, lon: lon, radius: radius)
    }
}

// MARK: - Analysis View

struct AnalysisView: View {
    @ObservedObject var viewModel: FloatsViewModel
    @State private var floatIdA = ""
    @State private var floatIdB = ""
    @State private var selectedChart = 0 // 0: TS, 1: TD
    
    var body: some View {
        ZStack {
            LinearGradient(gradient: Gradient(colors: [Color("BackgroundBlue"), Color("BackgroundBlueDark")]), startPoint: .top, endPoint: .bottom)
                .ignoresSafeArea()
            
            ScrollView {
                VStack(spacing: 20) {
                    Text("Comparative Analysis")
                        .font(.title2).bold()
                        .foregroundColor(.white)
                        .padding(.top, 56)
                    
                    VStack(spacing: 12) {
                        CoordinateField(title: "Float ID A", text: $floatIdA)
                        CoordinateField(title: "Float ID B (Optional)", text: $floatIdB)
                    }
                    .padding()
                    
                    Picker("Chart Type", selection: $selectedChart) {
                        Text("Temp-Salinity").tag(0)
                        Text("Temp-Depth").tag(1)
                    }
                    .pickerStyle(.segmented)
                    .padding(.horizontal)
                    .colorScheme(.dark)
                    
                    if !floatIdA.isEmpty {
                        VStack {
                            if floatIdB.isEmpty {
                                // Single Float Analysis
                                if selectedChart == 0 {
                                    AsyncImageView(url: viewModel.api.getTSCurveImageURL(floatId: floatIdA))
                                } else {
                                    AsyncImageView(url: viewModel.api.getTDCurveImageURL(floatId: floatIdA))
                                }
                            } else {
                                // Comparison
                                if selectedChart == 0 {
                                    AsyncImageView(url: viewModel.api.getCompareTSImageURL(floatIdA: floatIdA, floatIdB: floatIdB))
                                } else {
                                    AsyncImageView(url: viewModel.api.getCompareTDImageURL(floatIdA: floatIdA, floatIdB: floatIdB))
                                }
                            }
                        }
                        .padding()
                        .background(RoundedRectangle(cornerRadius: 18).fill(Color.white.opacity(0.1)))
                        .padding(.horizontal)
                    } else {
                        VStack(spacing: 12) {
                            Image(systemName: "chart.xyaxis.line")
                                .font(.largeTitle)
                                .foregroundColor(.white.opacity(0.5))
                            Text("Enter a Float ID to view analysis")
                                .foregroundColor(.white.opacity(0.5))
                        }
                        .frame(height: 200)
                        .frame(maxWidth: .infinity)
                        .background(RoundedRectangle(cornerRadius: 18).fill(Color.white.opacity(0.05)))
                        .padding()
                    }
                }
            }
        }
    }
}

// MARK: - Shared Components

struct AsyncImageView: View {
    let url: URL?
    
    var body: some View {
        if let url = url {
            AsyncImage(url: url) { phase in
                switch phase {
                case .empty:
                    ProgressView().tint(.white)
                        .frame(height: 250)
                case .success(let image):
                    image
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .cornerRadius(12)
                case .failure:
                    VStack {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.largeTitle)
                            .foregroundColor(.orange)
                        Text("Failed to load chart")
                            .foregroundColor(.white.opacity(0.7))
                    }
                    .frame(height: 250)
                @unknown default:
                    EmptyView()
                }
            }
        }
    }
}

struct FloatTile: View {
    let title: String
    let value: String
    let icon: String
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Image(systemName: icon)
                Text(title)
            }
            .foregroundColor(.white.opacity(0.8))
            .font(.subheadline)
            Text(value)
                .font(.title2).bold()
                .foregroundColor(.white)
        }
        .padding()
        .frame(width: 150, height: 80, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 14).fill(Color.white.opacity(0.13)).overlay(RoundedRectangle(cornerRadius: 14).stroke(Color.white.opacity(0.17), lineWidth: 1)))
    }
}

struct CoordinateField: View {
    let title: String
    @Binding var text: String

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .foregroundColor(.white.opacity(0.7))
                .font(.caption)
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.white.opacity(0.16))
                .frame(height: 44)
                .overlay(
                    TextField(title, text: $text)
                        .keyboardType(.decimalPad)
                        .foregroundColor(.white)
                        .accentColor(.white)
                        .padding(.horizontal, 10)
                )
        }
    }
}

struct FloatRow: View {
    let float: FloatSummary
    var onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            HStack {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Float \(float.floatId)")
                        .font(.headline)
                        .foregroundColor(.white)
                    Text("Lat: \(String(format: "%.2f", float.latitude)), Lon: \(String(format: "%.2f", float.longitude))")
                        .foregroundColor(.white.opacity(0.8))
                        .font(.caption)
                    if let distance = float.distanceKm {
                        Text("Distance: \(String(format: "%.0f", distance)) km")
                            .foregroundColor(.white.opacity(0.7))
                            .font(.caption2)
                    }
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .foregroundColor(.white.opacity(0.6))
            }
            .padding()
            .background(RoundedRectangle(cornerRadius: 16).fill(Color.white.opacity(0.1)))
        }
    }
}

struct FloatDetailsCard: View {
    let details: FloatDetailsResponse
    let viewModel: FloatsViewModel // Passed to access URL helpers

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Float \(details.floatId)")
                .font(.headline)
                .foregroundColor(.white)
            if let datetime = details.profile.datetime {
                Text("Last Update: \(datetime)")
                    .font(.caption)
                    .foregroundColor(.white.opacity(0.7))
            }
            HStack {
                FloatTile(title: "Cycle", value: "\(details.profile.cycleNumber ?? 0)", icon: "gauge")
                FloatTile(title: "Measurements", value: "\(details.measurementCount)", icon: "list.number")
            }
            
            Text("Recent Measurements")
                .font(.subheadline)
                .foregroundColor(.white.opacity(0.8))
                .padding(.top, 8)
            
            ForEach(details.measurements.prefix(3)) { measurement in
                VStack(alignment: .leading, spacing: 4) {
                    Text("Level \(measurement.level ?? 0)")
                        .foregroundColor(.white)
                    Text("Temp: \(measurement.temperature ?? 0, specifier: "%.2f")°C  |  Salinity: \(measurement.salinity ?? 0, specifier: "%.2f") PSU")
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.7))
                }
                .padding(8)
                .background(RoundedRectangle(cornerRadius: 12).fill(Color.white.opacity(0.08)))
            }
            
            // Embedded Charts
            Text("Quick Charts")
                .font(.subheadline)
                .foregroundColor(.white.opacity(0.8))
                .padding(.top, 8)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    VStack {
                        Text("TS Curve").font(.caption).foregroundColor(.white)
                        AsyncImageView(url: viewModel.api.getTSCurveImageURL(floatId: details.floatId))
                            .frame(width: 200, height: 150)
                    }
                    VStack {
                        Text("TD Curve").font(.caption).foregroundColor(.white)
                        AsyncImageView(url: viewModel.api.getTDCurveImageURL(floatId: details.floatId))
                            .frame(width: 200, height: 150)
                    }
                }
            }
        }
        .padding()
        .background(RoundedRectangle(cornerRadius: 18).fill(Color.white.opacity(0.1)))
    }
}

#Preview {
    ContentView()
}
