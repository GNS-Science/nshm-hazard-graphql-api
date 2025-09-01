# Changelog

## [0.2.3] - PENDING

### Changed
 - pinned import on graphql_server library to 3.0.0b7 until upstream release is fixed.
 - update to python 3.13 ECR image base to resolve pyproj build issues (and get better doc support)
 - updated upstream toshi-hazard-store

## [0.2.2] - 2025-07-23

### Changed
 - update to THS 1.2.1
 - migrate to THS hazard queries

## [0.2.1] - 2025-07-17

### Added
 - using THS 1.1.3 with out-of-bounds handling
 - test coverage for THS out-of-bounds exceptions

## [0.2.0] - 2025-07

### Added
 - support for dataset hazard queries in THS
 - tests to determine best THS query strategy

### Changed
 - Container packaging to support larger dependencies
 - using toshi-hazard-store @1.1.2

## [0.1.1]

### Changed
 - updated to toshi-hazard-store @0.7.5

## [0.1.0] - 2023-08-09

* factored hazard schema from kororaa-graphql-api project
