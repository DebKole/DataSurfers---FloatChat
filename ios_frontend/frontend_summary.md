# Frontend API Connection Summary

This document summarizes the API endpoints connected to the iOS frontend (`FloatAPI.swift` and `FloatsViewModel.swift`).

## Connected Endpoints

The following endpoints have been fully integrated into the iOS client:

### Float Data
- **Get Floats in Radius**: `GET /floats/radius`
  - Method: `fetchFloatsInRadius(lat:lon:radius:limit:)`
  - ViewModel: `fetchNearby(lat:lon:radius:)`
- **Get Indian Ocean Floats**: `GET /floats/indian-ocean`
  - Method: `fetchIndianOceanFloats(limit:)`
  - ViewModel: `fetchIndianOceanFloats(limit:)`
- **Get All Active Floats**: `GET /floats/all`
  - Method: `fetchAllFloats(limit:)`
  - ViewModel: `fetchAllFloats(limit:)`
- **Get Float Details**: `GET /floats/{float_id}`
  - Method: `fetchFloatDetails(id:minDepth:maxDepth:)`
  - ViewModel: `fetchFloatDetails(id:)`
- **Get Trajectories in Radius**: `GET /floats/trajectories/radius`
  - Method: `fetchTrajectoriesInRadius(lat:lon:radius:limit:)`
  - ViewModel: `fetchTrajectories(lat:lon:radius:)`

### Analysis & Charts
- **TS Curve Data**: `GET /api/ts_curve`
  - Method: `fetchTSCurve(floatId:limit:)`
  - ViewModel: `fetchTSCurve(floatId:)`
- **TD Curve Data**: `GET /api/td_curve`
  - Method: `fetchTDCurve(floatId:limit:)`
  - ViewModel: `fetchTDCurve(floatId:)`
- **Compare TS Data**: `GET /api/compare_ts`
  - Method: `compareTS(floatIdA:floatIdB:limit:)`
  - ViewModel: `compareTS(floatIdA:floatIdB:)`
- **Compare TD Data**: `GET /api/compare_td`
  - Method: `compareTD(floatIdA:floatIdB:limit:)`
  - ViewModel: `compareTD(floatIdA:floatIdB:)`

### Chart Images (URL Helpers)
- **TS Curve Image**: `GET /api/ts_curve_png`
  - Helper: `getTSCurveImageURL(floatId:limit:)`
- **TD Curve Image**: `GET /api/td_curve_png`
  - Helper: `getTDCurveImageURL(floatId:limit:)`
- **Compare TS Image**: `GET /api/compare_ts_png`
  - Helper: `getCompareTSImageURL(floatIdA:floatIdB:limit:)`
- **Compare TD Image**: `GET /api/compare_td_png`
  - Helper: `getCompareTDImageURL(floatIdA:floatIdB:limit:)`

### Chat & Info
- **Chat Query**: `POST /`
  - Method: `sendChatQuery(_:)`
  - ViewModel: `sendChatQuery(_:)`
- **Dataset Info**: `GET /dataset-info`
  - Method: `fetchDatasetInfo()`
  - ViewModel: `fetchDatasetInfo()`

## Unconnected Endpoints

- **Root Health Check**: `GET /`
  - Status: Not connected (Not required for frontend functionality)

## Notes
- All data endpoints use `Decodable` structs for type-safe parsing.
- Image endpoints are provided as URL generators for use with `AsyncImage` in SwiftUI.
- Error handling is implemented in `FloatAPI` and exposed via `errorMessage` in `FloatsViewModel`.
