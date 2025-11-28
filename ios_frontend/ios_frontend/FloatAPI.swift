import Foundation

enum FloatAPIError: LocalizedError {
    case invalidResponseStatus(Int, String?)
    case invalidURL
    case decodingFailed(Error)

    var errorDescription: String? {
        switch self {
        case .invalidResponseStatus(let status, let message):
            return "Request failed (\(status)): \(message ?? "Unknown error")"
        case .invalidURL:
            return "Failed to compose request URL."
        case .decodingFailed(let error):
            return "Unable to decode server response: \(error.localizedDescription)"
        }
    }
}

struct BackendConfig {
    static var baseURL = URL(string: "http://localhost:8000")!
}

struct RadiusResponse: Decodable {
    let status: Int
    let count: Int
    let floats: [FloatSummary]
    let center: LatLon
    let radiusKm: Double
}

struct LatLon: Decodable {
    let lat: Double
    let lon: Double
}

struct FloatSummary: Decodable, Identifiable, Equatable {
    let floatId: String
    let latitude: Double
    let longitude: Double
    let distanceKm: Double?
    let datetime: String?
    let cycleNumber: Int?
    let measurementCount: Int?
    let globalProfileId: Int?

    var id: String { floatId }
}

struct FloatDetailsResponse: Decodable {
    let status: Int
    let floatId: String
    let profile: FloatProfile
    let measurements: [FloatMeasurement]
    let measurementCount: Int
}

struct FloatProfile: Decodable {
    let globalProfileId: Int?
    let floatId: String
    let latitude: Double
    let longitude: Double
    let datetime: String?
    let cycleNumber: Int?
    let measurementCount: Int?
}

struct FloatMeasurement: Decodable, Identifiable {
    let id = UUID()
    let level: Int?
    let pressure: Double?
    let temperature: Double?
    let salinity: Double?
    let latitude: Double?
    let longitude: Double?
    let datetime: String?
    
    private enum CodingKeys: String, CodingKey {
        case level, pressure, temperature, salinity, latitude, longitude, datetime
    }
}

final class FloatAPI {
    private let baseURL: URL
    private let decoder: JSONDecoder

    init(baseURL: URL = BackendConfig.baseURL) {
        self.baseURL = baseURL
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.decoder = decoder
    }

    func fetchFloatsInRadius(lat: Double, lon: Double, radius: Double, limit: Int = 50) async throws -> RadiusResponse {
        guard var components = URLComponents(url: baseURL.appendingPathComponent("/floats/radius"), resolvingAgainstBaseURL: false) else {
            throw FloatAPIError.invalidURL
        }
        components.queryItems = [
            URLQueryItem(name: "lat", value: String(lat)),
            URLQueryItem(name: "lon", value: String(lon)),
            URLQueryItem(name: "radius", value: String(radius)),
            URLQueryItem(name: "limit", value: String(limit))
        ]
        guard let url = components.url else { throw FloatAPIError.invalidURL }

        let (data, _) = try await URLSession.shared.data(from: url)
        do {
            let response = try decoder.decode(RadiusResponse.self, from: data)
            guard response.status == 200 else {
                throw FloatAPIError.invalidResponseStatus(response.status, "Backend error")
            }
            return response
        } catch let decodingError {
            throw FloatAPIError.decodingFailed(decodingError)
        }
    }

    func fetchFloatDetails(id: String, minDepth: Int = 0, maxDepth: Int = 2000) async throws -> FloatDetailsResponse {
        guard var components = URLComponents(url: baseURL.appendingPathComponent("/floats/\(id)"), resolvingAgainstBaseURL: false) else {
            throw FloatAPIError.invalidURL
        }
        components.queryItems = [
            URLQueryItem(name: "min_depth", value: String(minDepth)),
            URLQueryItem(name: "max_depth", value: String(maxDepth))
        ]
        guard let url = components.url else { throw FloatAPIError.invalidURL }

        let (data, _) = try await URLSession.shared.data(from: url)
        do {
            let response = try decoder.decode(FloatDetailsResponse.self, from: data)
            guard response.status == 200 else {
                throw FloatAPIError.invalidResponseStatus(response.status, "Float not found")
            }
            return response
        } catch let decodingError {
            throw FloatAPIError.decodingFailed(decodingError)
        }
    }

    func fetchIndianOceanFloats(limit: Int = 50) async throws -> IndianOceanResponse {
        guard var components = URLComponents(url: baseURL.appendingPathComponent("/floats/indian-ocean"), resolvingAgainstBaseURL: false) else {
            throw FloatAPIError.invalidURL
        }
        components.queryItems = [
            URLQueryItem(name: "limit", value: String(limit))
        ]
        guard let url = components.url else { throw FloatAPIError.invalidURL }

        let (data, _) = try await URLSession.shared.data(from: url)
        do {
            let response = try decoder.decode(IndianOceanResponse.self, from: data)
            guard response.status == 200 else {
                throw FloatAPIError.invalidResponseStatus(response.status, "Backend error")
            }
            return response
        } catch let decodingError {
            throw FloatAPIError.decodingFailed(decodingError)
        }
    }

    func fetchAllFloats(limit: Int = 100) async throws -> AllFloatsResponse {
        guard var components = URLComponents(url: baseURL.appendingPathComponent("/floats/all"), resolvingAgainstBaseURL: false) else {
            throw FloatAPIError.invalidURL
        }
        components.queryItems = [
            URLQueryItem(name: "limit", value: String(limit))
        ]
        guard let url = components.url else { throw FloatAPIError.invalidURL }

        let (data, _) = try await URLSession.shared.data(from: url)
        do {
            let response = try decoder.decode(AllFloatsResponse.self, from: data)
            guard response.status == 200 else {
                throw FloatAPIError.invalidResponseStatus(response.status, "Backend error")
            }
            return response
        } catch let decodingError {
            throw FloatAPIError.decodingFailed(decodingError)
        }
    }

    func fetchTrajectoriesInRadius(lat: Double, lon: Double, radius: Double, limit: Int = 50) async throws -> TrajectoryResponse {
        guard var components = URLComponents(url: baseURL.appendingPathComponent("/floats/trajectories/radius"), resolvingAgainstBaseURL: false) else {
            throw FloatAPIError.invalidURL
        }
        components.queryItems = [
            URLQueryItem(name: "lat", value: String(lat)),
            URLQueryItem(name: "lon", value: String(lon)),
            URLQueryItem(name: "radius", value: String(radius)),
            URLQueryItem(name: "limit", value: String(limit))
        ]
        guard let url = components.url else { throw FloatAPIError.invalidURL }

        let (data, _) = try await URLSession.shared.data(from: url)
        do {
            let response = try decoder.decode(TrajectoryResponse.self, from: data)
            guard response.status == 200 else {
                throw FloatAPIError.invalidResponseStatus(response.status, "Backend error")
            }
            return response
        } catch let decodingError {
            throw FloatAPIError.decodingFailed(decodingError)
        }
    }

    func fetchDatasetInfo() async throws -> DatasetInfoResponse {
        let url = baseURL.appendingPathComponent("/dataset-info")
        let (data, _) = try await URLSession.shared.data(from: url)
        do {
            let response = try decoder.decode(DatasetInfoResponse.self, from: data)
            guard response.status == 200 else {
                throw FloatAPIError.invalidResponseStatus(response.status, "Backend error")
            }
            return response
        } catch let decodingError {
            throw FloatAPIError.decodingFailed(decodingError)
        }
    }

    func sendChatQuery(_ query: String) async throws -> ChatQueryResponse {
        let url = baseURL.appendingPathComponent("/")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ChatQueryRequest(query: query)
        request.httpBody = try JSONEncoder().encode(body)

        let (data, _) = try await URLSession.shared.data(for: request)
        do {
            let response = try decoder.decode(ChatQueryResponse.self, from: data)
            guard response.status == 201 else {
                throw FloatAPIError.invalidResponseStatus(response.status, "Backend error")
            }
            return response
        } catch let decodingError {
            throw FloatAPIError.decodingFailed(decodingError)
        }
    }

    // MARK: - Analysis Endpoints

    func fetchTSCurve(floatId: String, limit: Int = 200) async throws -> ProfilesResponse {
        guard var components = URLComponents(url: baseURL.appendingPathComponent("/api/ts_curve"), resolvingAgainstBaseURL: false) else {
            throw FloatAPIError.invalidURL
        }
        components.queryItems = [
            URLQueryItem(name: "float_id", value: floatId),
            URLQueryItem(name: "limit", value: String(limit))
        ]
        guard let url = components.url else { throw FloatAPIError.invalidURL }

        let (data, _) = try await URLSession.shared.data(from: url)
        return try decoder.decode(ProfilesResponse.self, from: data)
    }

    func fetchTDCurve(floatId: String, limit: Int = 200) async throws -> ProfilesResponse {
        guard var components = URLComponents(url: baseURL.appendingPathComponent("/api/td_curve"), resolvingAgainstBaseURL: false) else {
            throw FloatAPIError.invalidURL
        }
        components.queryItems = [
            URLQueryItem(name: "float_id", value: floatId),
            URLQueryItem(name: "limit", value: String(limit))
        ]
        guard let url = components.url else { throw FloatAPIError.invalidURL }

        let (data, _) = try await URLSession.shared.data(from: url)
        return try decoder.decode(ProfilesResponse.self, from: data)
    }

    func compareTS(floatIdA: String, floatIdB: String, limit: Int = 200) async throws -> ProfilesResponse {
        guard var components = URLComponents(url: baseURL.appendingPathComponent("/api/compare_ts"), resolvingAgainstBaseURL: false) else {
            throw FloatAPIError.invalidURL
        }
        components.queryItems = [
            URLQueryItem(name: "float_id_a", value: floatIdA),
            URLQueryItem(name: "float_id_b", value: floatIdB),
            URLQueryItem(name: "limit", value: String(limit))
        ]
        guard let url = components.url else { throw FloatAPIError.invalidURL }

        let (data, _) = try await URLSession.shared.data(from: url)
        return try decoder.decode(ProfilesResponse.self, from: data)
    }

    func compareTD(floatIdA: String, floatIdB: String, limit: Int = 200) async throws -> ProfilesResponse {
        guard var components = URLComponents(url: baseURL.appendingPathComponent("/api/compare_td"), resolvingAgainstBaseURL: false) else {
            throw FloatAPIError.invalidURL
        }
        components.queryItems = [
            URLQueryItem(name: "float_id_a", value: floatIdA),
            URLQueryItem(name: "float_id_b", value: floatIdB),
            URLQueryItem(name: "limit", value: String(limit))
        ]
        guard let url = components.url else { throw FloatAPIError.invalidURL }

        let (data, _) = try await URLSession.shared.data(from: url)
        return try decoder.decode(ProfilesResponse.self, from: data)
    }

    // MARK: - Image URL Helpers

    func getTSCurveImageURL(floatId: String, limit: Int = 200) -> URL? {
        var components = URLComponents(url: baseURL.appendingPathComponent("/api/ts_curve_png"), resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "float_id", value: floatId),
            URLQueryItem(name: "limit", value: String(limit))
        ]
        return components?.url
    }

    func getTDCurveImageURL(floatId: String, limit: Int = 200) -> URL? {
        var components = URLComponents(url: baseURL.appendingPathComponent("/api/td_curve_png"), resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "float_id", value: floatId),
            URLQueryItem(name: "limit", value: String(limit))
        ]
        return components?.url
    }

    func getCompareTSImageURL(floatIdA: String, floatIdB: String, limit: Int = 200) -> URL? {
        var components = URLComponents(url: baseURL.appendingPathComponent("/api/compare_ts_png"), resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "float_id_a", value: floatIdA),
            URLQueryItem(name: "float_id_b", value: floatIdB),
            URLQueryItem(name: "limit", value: String(limit))
        ]
        return components?.url
    }

    func getCompareTDImageURL(floatIdA: String, floatIdB: String, limit: Int = 200) -> URL? {
        var components = URLComponents(url: baseURL.appendingPathComponent("/api/compare_td_png"), resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "float_id_a", value: floatIdA),
            URLQueryItem(name: "float_id_b", value: floatIdB),
            URLQueryItem(name: "limit", value: String(limit))
        ]
        return components?.url
    }
}

// MARK: - Response Structs

struct IndianOceanResponse: Decodable {
    let status: Int
    let count: Int
    let floats: [FloatSummary]
    let region: String
    let bounds: RegionBounds
}

struct RegionBounds: Decodable {
    let lat: [Double]
    let lng: [Double]
}

struct AllFloatsResponse: Decodable {
    let status: Int
    let count: Int
    let floats: [FloatSummary]
    let dataPeriod: String
}

struct TrajectoryResponse: Decodable {
    let status: Int
    let count: Int
    let trajectories: [TrajectoryPoint]
    let center: LatLon
    let radiusKm: Double
}

struct TrajectoryPoint: Decodable, Identifiable {
    let profileId: Int
    let lat: Double
    let lon: Double
    let floatId: String
    let cycleNumber: Int?
    let datetime: String?
    
    var id: Int { profileId }
}

struct DatasetInfoResponse: Decodable {
    let status: Int
    let data: DatasetStats
}

struct DatasetStats: Decodable {
    let totalProfiles: Int
    let totalMeasurements: Int
    let depthRange: String
    let temperatureRange: String
    let salinityRange: String
    let pressureRange: String
    let location: String
}

struct ChatQueryRequest: Encodable {
    let query: String
}

struct ChatQueryResponse: Decodable {
    let status: Int
    let message: String
    let queryType: String
    let hasData: Bool
    let showMap: Bool
}

struct ProfilesResponse: Decodable {
    let profiles: [AnalysisProfile]
}

struct AnalysisProfile: Decodable {
    let floatId: String?
    let measurements: [AnalysisMeasurement]?
}

struct AnalysisMeasurement: Decodable {
    let pressure: Double?
    let temperature: Double?
    let salinity: Double?
    let depth: Double?
}
