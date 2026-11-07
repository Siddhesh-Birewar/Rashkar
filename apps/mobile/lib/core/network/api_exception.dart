/// CropNet AI — Network Exception Hierarchy
///
/// Encapsulates all network, HTTP status code, and serialization errors
/// with typed context and diagnostic details.
abstract class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final dynamic details;

  const ApiException({
    required this.message,
    this.statusCode,
    this.details,
  });

  @override
  String toString() {
    if (statusCode != null) {
      return '$runtimeType (Status $statusCode): $message';
    }
    return '$runtimeType: $message';
  }
}

/// Thrown when request parameter or payload validation fails (HTTP 400).
class BadRequestException extends ApiException {
  const BadRequestException({
    super.message = 'Bad Request: The server could not understand the request',
    super.details,
  }) : super(statusCode: 400);
}

/// Thrown when authentication is missing or token is invalid/expired (HTTP 401).
class UnauthorizedException extends ApiException {
  const UnauthorizedException({
    super.message = 'Unauthorized: Authentication required or token expired',
    super.details,
  }) : super(statusCode: 401);
}

/// Thrown when the caller does not have permission to access the resource (HTTP 403).
class ForbiddenException extends ApiException {
  const ForbiddenException({
    super.message = 'Forbidden: Access to this agricultural resource is denied',
    super.details,
  }) : super(statusCode: 403);
}

/// Thrown when the requested resource (farm, crop, soil profile, decision) does not exist (HTTP 404).
class NotFoundException extends ApiException {
  const NotFoundException({
    super.message = 'Not Found: The requested resource does not exist',
    super.details,
  }) : super(statusCode: 404);
}

/// Thrown when FastAPI schema validation fails (HTTP 422 Unprocessable Entity).
class ValidationException extends ApiException {
  final List<dynamic>? validationErrors;

  const ValidationException({
    super.message = 'Validation Error: Request payload failed schema validation',
    this.validationErrors,
    super.details,
  }) : super(statusCode: 422);

  @override
  String toString() {
    if (validationErrors != null && validationErrors!.isNotEmpty) {
      return '$runtimeType (Status 422): $message (Errors: $validationErrors)';
    }
    return super.toString();
  }
}

/// Thrown on backend internal errors (HTTP 500+).
class ServerException extends ApiException {
  const ServerException({
    super.message = 'Internal Server Error: Backend service encountered an unexpected error',
    super.statusCode = 500,
    super.details,
  });
}

/// Thrown on connectivity issues (DNS failure, connection refused, offline).
class NetworkException extends ApiException {
  const NetworkException({
    super.message = 'Network Error: Unable to establish connection to CropNet backend',
    super.details,
  });
}

/// Thrown when an HTTP request exceeds the configured timeout duration.
class RequestTimeoutException extends ApiException {
  final Duration timeout;

  const RequestTimeoutException({
    required this.timeout,
    super.message = 'Request Timeout: CropNet server did not respond within the allocated time',
    super.details,
  });

  @override
  String toString() => '$runtimeType: $message (${timeout.inSeconds}s)';
}

/// Thrown when server response fails JSON decoding or schema mapping.
class JsonParseException extends ApiException {
  const JsonParseException({
    super.message = 'JSON Parse Error: Unable to decode server response payload',
    super.details,
  });
}
