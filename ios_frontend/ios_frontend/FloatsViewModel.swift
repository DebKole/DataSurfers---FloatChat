import Foundation
import Combine

@MainActor
final class FloatsViewModel: ObservableObject {
    @Published var floats: [FloatSummary] = []
    @Published var floatDetails: FloatDetailsResponse?
    @Published var isLoadingNearby = false
    @Published var isLoadingDetails = false
    @Published var errorMessage: String?

    @Published var trajectories: [TrajectoryPoint] = []
    @Published var datasetInfo: DatasetStats?
    @Published var chatResponse: ChatQueryResponse?
    @Published var analysisResult: ProfilesResponse?
    
    @Published var isLoadingTrajectories = false
    @Published var isLoadingAnalysis = false
    @Published var isLoadingChat = false

    let api: FloatAPI

    init(api: FloatAPI = FloatAPI()) {
        self.api = api
    }

    func fetchNearby(lat: Double, lon: Double, radius: Double) async {
        isLoadingNearby = true
        errorMessage = nil
        defer { isLoadingNearby = false }

        do {
            let response = try await api.fetchFloatsInRadius(lat: lat, lon: lon, radius: radius)
            floats = response.floats
        } catch {
            errorMessage = error.localizedDescription
        }
    }
    
    func fetchIndianOceanFloats(limit: Int = 50) async {
        isLoadingNearby = true
        errorMessage = nil
        defer { isLoadingNearby = false }
        
        do {
            let response = try await api.fetchIndianOceanFloats(limit: limit)
            floats = response.floats
        } catch {
            errorMessage = error.localizedDescription
        }
    }
    
    func fetchAllFloats(limit: Int = 100) async {
        isLoadingNearby = true
        errorMessage = nil
        defer { isLoadingNearby = false }
        
        do {
            let response = try await api.fetchAllFloats(limit: limit)
            floats = response.floats
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func fetchFloatDetails(id: String) async {
        guard !id.isEmpty else { return }
        isLoadingDetails = true
        errorMessage = nil
        defer { isLoadingDetails = false }

        do {
            let details = try await api.fetchFloatDetails(id: id)
            floatDetails = details
        } catch {
            errorMessage = error.localizedDescription
        }
    }
    
    func fetchTrajectories(lat: Double, lon: Double, radius: Double) async {
        isLoadingTrajectories = true
        errorMessage = nil
        defer { isLoadingTrajectories = false }
        
        do {
            let response = try await api.fetchTrajectoriesInRadius(lat: lat, lon: lon, radius: radius)
            trajectories = response.trajectories
        } catch {
            errorMessage = error.localizedDescription
        }
    }
    
    func fetchDatasetInfo() async {
        errorMessage = nil
        do {
            let response = try await api.fetchDatasetInfo()
            datasetInfo = response.data
        } catch {
            errorMessage = error.localizedDescription
        }
    }
    
    func sendChatQuery(_ query: String) async {
        isLoadingChat = true
        errorMessage = nil
        defer { isLoadingChat = false }
        
        do {
            let response = try await api.sendChatQuery(query)
            chatResponse = response
        } catch {
            errorMessage = error.localizedDescription
        }
    }
    
    func fetchTSCurve(floatId: String) async {
        isLoadingAnalysis = true
        errorMessage = nil
        defer { isLoadingAnalysis = false }
        
        do {
            let response = try await api.fetchTSCurve(floatId: floatId)
            analysisResult = response
        } catch {
            errorMessage = error.localizedDescription
        }
    }
    
    func fetchTDCurve(floatId: String) async {
        isLoadingAnalysis = true
        errorMessage = nil
        defer { isLoadingAnalysis = false }
        
        do {
            let response = try await api.fetchTDCurve(floatId: floatId)
            analysisResult = response
        } catch {
            errorMessage = error.localizedDescription
        }
    }
    
    func compareTS(floatIdA: String, floatIdB: String) async {
        isLoadingAnalysis = true
        errorMessage = nil
        defer { isLoadingAnalysis = false }
        
        do {
            let response = try await api.compareTS(floatIdA: floatIdA, floatIdB: floatIdB)
            analysisResult = response
        } catch {
            errorMessage = error.localizedDescription
        }
    }
    
    func compareTD(floatIdA: String, floatIdB: String) async {
        isLoadingAnalysis = true
        errorMessage = nil
        defer { isLoadingAnalysis = false }
        
        do {
            let response = try await api.compareTD(floatIdA: floatIdA, floatIdB: floatIdB)
            analysisResult = response
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
