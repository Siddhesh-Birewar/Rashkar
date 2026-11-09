import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

import 'api_constants.dart';
import 'api_exception.dart';

/// Callback signature for dynamic authentication token acquisition (e.g. Supabase JWT).
typedef AuthTokenProvider = FutureOr<String?> Function();

/// Reusable HTTP client and networking core for CropNet AI.
///
/// Features:
/// - Environment-aware base URL configuration
/// - Bearer token and development user ID header injection
/// - Dynamic authentication token provider support (Supabase session)
/// - Standardized timeout execution (default 30 seconds)
/// - Robust HTTP status code mapping (400, 401, 403, 404, 422, 500+)
/// - Safe JSON serialization/deserialization with error trapping
/// - Pluggable [http.Client] for seamless unit and integration testing
class ApiClient {
  /// Global default token provider injected by authentication service.
  static AuthTokenProvider? defaultAuthTokenProvider;

  final String baseUrl;
  final http.Client _httpClient;
  final Duration defaultTimeout;
  String? bearerToken;
  String? devUserId;
  final AuthTokenProvider? authTokenProvider;

  ApiClient({
    String? baseUrl,
    http.Client? httpClient,
    this.defaultTimeout = const Duration(seconds: 30),
    this.bearerToken,
    this.devUserId = ApiConstants.defaultDevUserId,
    this.authTokenProvider,
  })  : baseUrl = (baseUrl ?? ApiConstants.defaultBaseUrl).replaceAll(RegExp(r'/+$'), ''),
        _httpClient = httpClient ?? http.Client();

  /// Build URI merging [baseUrl], [path], and [queryParameters].
  Uri _buildUri(String path, [Map<String, dynamic>? queryParameters]) {
    final cleanPath = path.startsWith('/') ? path : '/$path';
    final fullUrl = '$baseUrl$cleanPath';

    if (queryParameters == null || queryParameters.isEmpty) {
      return Uri.parse(fullUrl);
    }

    final sanitizedParams = <String, dynamic>{};
    for (final entry in queryParameters.entries) {
      if (entry.value != null) {
        if (entry.value is Iterable) {
          sanitizedParams[entry.key] = (entry.value as Iterable).map((e) => e.toString()).toList();
        } else {
          sanitizedParams[entry.key] = entry.value.toString();
        }
      }
    }

    return Uri.parse(fullUrl).replace(queryParameters: sanitizedParams.isEmpty ? null : sanitizedParams);
  }

  /// Build default HTTP headers including content type and auth headers.
  Future<Map<String, String>> _buildHeaders(Map<String, String>? customHeaders) async {
    final headers = <String, String>{
      'Content-Type': 'application/json; charset=utf-8',
      'Accept': 'application/json',
    };

    String? token = bearerToken;
    final provider = authTokenProvider ?? defaultAuthTokenProvider;
    if (provider != null) {
      try {
        token = await provider();
      } catch (_) {
        // Fallback to static bearerToken if provider fails
      }
    }

    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    } else if (devUserId != null && devUserId!.isNotEmpty) {
      headers[ApiConstants.devUserIdHeader] = devUserId!;
    }

    if (customHeaders != null) {
      headers.addAll(customHeaders);
    }

    return headers;
  }

  /// Standard HTTP GET
  Future<T> get<T>(
    String path, {
    Map<String, String>? headers,
    Map<String, dynamic>? queryParameters,
    Duration? timeout,
    T Function(dynamic json)? fromJson,
  }) async {
    final uri = _buildUri(path, queryParameters);
    final requestHeaders = await _buildHeaders(headers);
    return _send<T>(
      () => _httpClient.get(uri, headers: requestHeaders),
      timeout: timeout ?? defaultTimeout,
      fromJson: fromJson,
    );
  }

  /// Standard HTTP POST
  Future<T> post<T>(
    String path, {
    dynamic body,
    Map<String, String>? headers,
    Map<String, dynamic>? queryParameters,
    Duration? timeout,
    T Function(dynamic json)? fromJson,
  }) async {
    final uri = _buildUri(path, queryParameters);
    final requestHeaders = await _buildHeaders(headers);
    final encodedBody = body != null ? jsonEncode(body) : null;
    return _send<T>(
      () => _httpClient.post(uri, headers: requestHeaders, body: encodedBody),
      timeout: timeout ?? defaultTimeout,
      fromJson: fromJson,
    );
  }

  /// Standard HTTP PUT
  Future<T> put<T>(
    String path, {
    dynamic body,
    Map<String, String>? headers,
    Map<String, dynamic>? queryParameters,
    Duration? timeout,
    T Function(dynamic json)? fromJson,
  }) async {
    final uri = _buildUri(path, queryParameters);
    final requestHeaders = await _buildHeaders(headers);
    final encodedBody = body != null ? jsonEncode(body) : null;
    return _send<T>(
      () => _httpClient.put(uri, headers: requestHeaders, body: encodedBody),
      timeout: timeout ?? defaultTimeout,
      fromJson: fromJson,
    );
  }

  /// Standard HTTP DELETE
  Future<T> delete<T>(
    String path, {
    Map<String, String>? headers,
    Map<String, dynamic>? queryParameters,
    Duration? timeout,
    T Function(dynamic json)? fromJson,
  }) async {
    final uri = _buildUri(path, queryParameters);
    final requestHeaders = await _buildHeaders(headers);
    return _send<T>(
      () => _httpClient.delete(uri, headers: requestHeaders),
      timeout: timeout ?? defaultTimeout,
      fromJson: fromJson,
    );
  }

  /// Execute an HTTP request with error mapping and timeout handling.
  Future<T> _send<T>(
    Future<http.Response> Function() requestFn, {
    required Duration timeout,
    T Function(dynamic json)? fromJson,
  }) async {
    http.Response response;
    try {
      response = await requestFn().timeout(timeout);
    } on TimeoutException catch (e) {
      throw RequestTimeoutException(timeout: timeout, details: e);
    } on http.ClientException catch (e) {
      throw NetworkException(message: 'Connection failed: ${e.message}', details: e);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw NetworkException(message: 'Unexpected network error: $e', details: e);
    }

    return _processResponse<T>(response, fromJson);
  }

  /// Parse and validate HTTP response.
  T _processResponse<T>(http.Response response, T Function(dynamic json)? fromJson) {
    final statusCode = response.statusCode;

    // 204 No Content
    if (statusCode == 204) {
      if (fromJson != null) {
        return fromJson(null);
      }
      return null as T;
    }

    dynamic decodedBody;
    String rawBody;
    try {
      rawBody = utf8.decode(response.bodyBytes);
    } catch (_) {
      rawBody = response.body;
    }

    if (rawBody.isNotEmpty) {
      try {
        decodedBody = jsonDecode(rawBody);
      } catch (e) {
        if (statusCode >= 200 && statusCode < 300) {
          throw JsonParseException(
            message: 'Failed to decode JSON response from server',
            details: e,
          );
        }
        decodedBody = rawBody;
      }
    }

    if (statusCode >= 200 && statusCode < 300) {
      if (fromJson != null) {
        try {
          return fromJson(decodedBody);
        } catch (e) {
          throw JsonParseException(
            message: 'Failed to map response JSON to ${T.toString()}: $e',
            details: e,
          );
        }
      }
      return decodedBody as T;
    }

    // Handle HTTP error responses
    final errorMessage = _extractErrorMessage(decodedBody) ??
        'HTTP Request failed with status code $statusCode';

    switch (statusCode) {
      case 400:
        throw BadRequestException(message: errorMessage, details: decodedBody);
      case 401:
        throw UnauthorizedException(message: errorMessage, details: decodedBody);
      case 403:
        throw ForbiddenException(message: errorMessage, details: decodedBody);
      case 404:
        throw NotFoundException(message: errorMessage, details: decodedBody);
      case 422:
        List<dynamic>? errors;
        if (decodedBody is Map && decodedBody['detail'] is List) {
          errors = decodedBody['detail'] as List<dynamic>;
        }
        throw ValidationException(
          message: errorMessage,
          validationErrors: errors,
          details: decodedBody,
        );
      default:
        if (statusCode >= 500) {
          throw ServerException(
            message: errorMessage,
            statusCode: statusCode,
            details: decodedBody,
          );
        }
        throw BadRequestException(
          message: errorMessage,
          details: decodedBody,
        );
    }
  }

  /// Extract human-readable error detail from FastAPI response body.
  String? _extractErrorMessage(dynamic body) {
    if (body is Map) {
      if (body['detail'] is String) {
        return body['detail'] as String;
      }
      if (body['detail'] is List) {
        final list = body['detail'] as List;
        if (list.isNotEmpty && list.first is Map && list.first['msg'] is String) {
          return list.map((e) => '${e['loc']?.join('.')}: ${e['msg']}').join('; ');
        }
      }
      if (body['message'] is String) {
        return body['message'] as String;
      }
      if (body['error'] is String) {
        return body['error'] as String;
      }
    }
    return null;
  }

  /// Closes the underlying HTTP client.
  void close() {
    _httpClient.close();
  }
}
