import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:cropnet_mobile/core/network/api_client.dart';
import 'package:cropnet_mobile/core/network/api_constants.dart';
import 'package:cropnet_mobile/core/network/api_exception.dart';

void main() {
  group('ApiClient Tests', () {
    test('Default headers do not inject X-Dev-User-Id unless explicitly configured', () async {
      late http.Request capturedRequest;

      final mockClient = MockClient((request) async {
        capturedRequest = request;
        return http.Response(jsonEncode({'status': 'ok'}), 200);
      });

      final client = ApiClient(
        baseUrl: 'http://localhost:8000',
        httpClient: mockClient,
      );

      final result = await client.get<Map<String, dynamic>>('/api/v1/health');

      expect(result['status'], 'ok');
      expect(capturedRequest.headers.containsKey(ApiConstants.devUserIdHeader), false);
      expect(capturedRequest.headers['Content-Type'], 'application/json; charset=utf-8');
      expect(capturedRequest.headers['Accept'], 'application/json');
    });

    test('Explicit devUserId injects X-Dev-User-Id header for local dev', () async {
      late http.Request capturedRequest;

      final mockClient = MockClient((request) async {
        capturedRequest = request;
        return http.Response(jsonEncode({'status': 'ok'}), 200);
      });

      final client = ApiClient(
        baseUrl: 'http://localhost:8000',
        httpClient: mockClient,
        devUserId: ApiConstants.defaultDevUserId,
      );

      final result = await client.get<Map<String, dynamic>>('/api/v1/health');

      expect(result['status'], 'ok');
      expect(capturedRequest.headers[ApiConstants.devUserIdHeader], ApiConstants.defaultDevUserId);
    });

    test('Token acquisition failure throws UnauthorizedException and never injects X-Dev-User-Id', () async {
      final mockClient = MockClient((request) async {
        return http.Response(jsonEncode({'status': 'ok'}), 200);
      });

      final client = ApiClient(
        baseUrl: 'http://localhost:8000',
        httpClient: mockClient,
        devUserId: ApiConstants.defaultDevUserId,
        authTokenProvider: () => throw Exception('Supabase token expired'),
      );

      expect(
        () => client.get('/api/v1/health'),
        throwsA(isA<UnauthorizedException>().having(
          (e) => e.message,
          'message',
          contains('Authentication token acquisition failed'),
        )),
      );
    });

    test('Bearer token overrides dev user ID when provided', () async {
      late http.Request capturedRequest;

      final mockClient = MockClient((request) async {
        capturedRequest = request;
        return http.Response(jsonEncode({'status': 'ok'}), 200);
      });

      final client = ApiClient(
        baseUrl: 'http://localhost:8000',
        httpClient: mockClient,
        bearerToken: 'test-jwt-token-xyz',
      );

      await client.get<Map<String, dynamic>>('/api/v1/health');

      expect(capturedRequest.headers['Authorization'], 'Bearer test-jwt-token-xyz');
      expect(capturedRequest.headers.containsKey(ApiConstants.devUserIdHeader), false);
    });

    test('Query parameters are correctly serialized', () async {
      late http.Request capturedRequest;

      final mockClient = MockClient((request) async {
        capturedRequest = request;
        return http.Response(jsonEncode([]), 200);
      });

      final client = ApiClient(
        baseUrl: 'http://localhost:8000',
        httpClient: mockClient,
      );

      await client.get<List<dynamic>>(
        '/api/v1/crops',
        queryParameters: {'category': 'Pulse', 'season': 'Rabi'},
      );

      expect(capturedRequest.url.queryParameters['category'], 'Pulse');
      expect(capturedRequest.url.queryParameters['season'], 'Rabi');
    });

    test('Maps HTTP 400 to BadRequestException', () async {
      final mockClient = MockClient((request) async {
        return http.Response(jsonEncode({'detail': 'Invalid polygon coordinates'}), 400);
      });

      final client = ApiClient(httpClient: mockClient);

      expect(
        () => client.get('/test'),
        throwsA(isA<BadRequestException>().having(
          (e) => e.message,
          'message',
          contains('Invalid polygon coordinates'),
        )),
      );
    });

    test('Maps HTTP 401 to UnauthorizedException', () async {
      final mockClient = MockClient((request) async {
        return http.Response(jsonEncode({'detail': 'Missing Authorization Bearer token'}), 401);
      });

      final client = ApiClient(httpClient: mockClient);

      expect(
        () => client.get('/test'),
        throwsA(isA<UnauthorizedException>().having(
          (e) => e.statusCode,
          'statusCode',
          401,
        )),
      );
    });

    test('Maps HTTP 403 to ForbiddenException', () async {
      final mockClient = MockClient((request) async {
        return http.Response(
          jsonEncode({'detail': 'You do not have permission to access this farm'}),
          403,
        );
      });

      final client = ApiClient(httpClient: mockClient);

      expect(
        () => client.get('/test'),
        throwsA(isA<ForbiddenException>()),
      );
    });

    test('Maps HTTP 404 to NotFoundException', () async {
      final mockClient = MockClient((request) async {
        return http.Response(jsonEncode({'detail': 'Farm not found'}), 404);
      });

      final client = ApiClient(httpClient: mockClient);

      expect(
        () => client.get('/test'),
        throwsA(isA<NotFoundException>()),
      );
    });

    test('Maps HTTP 422 to ValidationException with extracted error locations', () async {
      final mockClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'detail': [
              {
                'loc': ['body', 'soil_ph'],
                'msg': 'Input should be greater than or equal to 3.0',
                'type': 'greater_than_equal',
              }
            ]
          }),
          422,
        );
      });

      final client = ApiClient(httpClient: mockClient);

      expect(
        () => client.post('/test', body: {'soil_ph': 2.0}),
        throwsA(isA<ValidationException>().having(
          (e) => e.validationErrors?.first['loc'],
          'error location',
          contains('soil_ph'),
        )),
      );
    });

    test('Maps HTTP 500 to ServerException', () async {
      final mockClient = MockClient((request) async {
        return http.Response(jsonEncode({'detail': 'Database connection error'}), 500);
      });

      final client = ApiClient(httpClient: mockClient);

      expect(
        () => client.get('/test'),
        throwsA(isA<ServerException>().having(
          (e) => e.statusCode,
          'statusCode',
          500,
        )),
      );
    });

    test('Throws JsonParseException when response JSON is invalid', () async {
      final mockClient = MockClient((request) async {
        return http.Response('not valid json {', 200);
      });

      final client = ApiClient(httpClient: mockClient);

      expect(
        () => client.get<Map<String, dynamic>>('/test'),
        throwsA(isA<JsonParseException>()),
      );
    });

    test('Processes HTTP 204 No Content cleanly', () async {
      final mockClient = MockClient((request) async {
        return http.Response('', 204);
      });

      final client = ApiClient(httpClient: mockClient);

      await client.delete<void>('/api/v1/farms/123');
    });
  });
}
