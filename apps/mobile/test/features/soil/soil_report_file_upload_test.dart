import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:cropnet_mobile/core/network/api_client.dart';
import 'package:cropnet_mobile/core/router/route_paths.dart';
import 'package:cropnet_mobile/features/soil/data/soil_lab_repository.dart';
import 'package:cropnet_mobile/features/soil/presentation/screens/soil_report_upload_screen.dart';
import 'package:cropnet_mobile/features/soil/presentation/state/soil_lab_notifier.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('DocumentFileValidator Unit Tests', () {
    test('Validates authentic PDF header bytes', () {
      final validPdfBytes = utf8.encode('%PDF-1.4 sample baramati lab report');
      final result = DocumentFileValidator.validate(
        filename: 'Soil_Health_Card.pdf',
        bytes: validPdfBytes,
      );
      expect(result.isValid, isTrue);
      expect(result.mimeType, equals('application/pdf'));
      expect(result.errorMessage, isNull);
    });

    test('Validates PDF with offset header comment within 1024 bytes', () {
      final offsetPdf = [
        ...List<int>.filled(64, 0x20), // leading spaces
        0x25, 0x50, 0x44, 0x46, // %PDF
        ...utf8.encode('-1.5 binary stream data'),
      ];
      final result = DocumentFileValidator.validate(
        filename: 'Scanned_Card.pdf',
        bytes: offsetPdf,
      );
      expect(result.isValid, isTrue);
      expect(result.mimeType, equals('application/pdf'));
    });

    test('Validates authentic JPEG SOI marker', () {
      final jpegBytes = [0xFF, 0xD8, 0xFF, 0xE0, ...utf8.encode('jpeg photo data')];
      final result = DocumentFileValidator.validate(
        filename: 'lab_scan.jpg',
        bytes: jpegBytes,
      );
      expect(result.isValid, isTrue);
      expect(result.mimeType, equals('image/jpeg'));
    });

    test('Validates authentic PNG magic bytes', () {
      final pngBytes = [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, ...utf8.encode('png chunk data')];
      final result = DocumentFileValidator.validate(
        filename: 'lab_scan.png',
        bytes: pngBytes,
      );
      expect(result.isValid, isTrue);
      expect(result.mimeType, equals('image/png'));
    });

    test('Rejects empty 0-byte document', () {
      final result = DocumentFileValidator.validate(
        filename: 'empty.pdf',
        bytes: [],
        sizeBytes: 0,
      );
      expect(result.isValid, isFalse);
      expect(result.errorMessage, contains('Selected file is empty (0 bytes)'));
    });

    test('Rejects document exceeding 15MB limit', () {
      final result = DocumentFileValidator.validate(
        filename: 'huge_scan.pdf',
        bytes: [0x25, 0x50, 0x44, 0x46],
        sizeBytes: 15 * 1024 * 1024 + 1024,
      );
      expect(result.isValid, isFalse);
      expect(result.errorMessage, contains('exceeds the maximum 15 MB limit'));
    });

    test('Rejects spoofed PDF with text contents', () {
      final spoofed = utf8.encode('plain text masquerading as pdf');
      final result = DocumentFileValidator.validate(
        filename: 'malicious.pdf',
        bytes: spoofed,
      );
      expect(result.isValid, isFalse);
      expect(result.errorMessage, contains('signature does not match'));
    });

    test('Rejects spoofed JPEG with text contents', () {
      final spoofed = utf8.encode('plain text masquerading as jpeg');
      final result = DocumentFileValidator.validate(
        filename: 'malicious.jpeg',
        bytes: spoofed,
      );
      expect(result.isValid, isFalse);
      expect(result.errorMessage, contains('signature does not match'));
    });

    test('Rejects spoofed PNG with text contents', () {
      final spoofed = utf8.encode('plain text masquerading as png');
      final result = DocumentFileValidator.validate(
        filename: 'malicious.png',
        bytes: spoofed,
      );
      expect(result.isValid, isFalse);
      expect(result.errorMessage, contains('signature does not match'));
    });

    test('Rejects unsupported extension', () {
      final bytes = utf8.encode('some document content');
      final result = DocumentFileValidator.validate(
        filename: 'report.docx',
        bytes: bytes,
      );
      expect(result.isValid, isFalse);
      expect(result.errorMessage, contains('Unsupported document format'));
    });
  });

  group('SoilReportUploadScreen Interactive Widget Tests', () {
    testWidgets('Initial empty state has disabled upload button and Browse Document', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: SoilReportUploadScreen(farmId: 'farm-101'),
        ),
      );

      expect(find.text('Upload Soil Test Document'), findsOneWidget);
      expect(find.text('Browse Document'), findsOneWidget);

      final uploadBtnFinder = find.widgetWithText(ElevatedButton, 'Upload & Extract Soil Parameters');
      expect(uploadBtnFinder, findsOneWidget);
      final btn = tester.widget<ElevatedButton>(uploadBtnFinder);
      expect(btn.onPressed, isNull); // disabled
    });

    testWidgets('Selecting valid PDF populates file info, enables upload button and allows removal', (tester) async {
      final validPdf = UploadDocumentFile(
        name: 'Pune_KVK_Soil_Report.pdf',
        bytes: utf8.encode('%PDF-1.4 official report data'),
        mimeType: 'application/pdf',
        sizeBytes: 450000,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: SoilReportUploadScreen(
            farmId: 'farm-101',
            customFilePicker: () async => validPdf,
          ),
        ),
      );

      // Tap Browse Document button
      await tester.tap(find.text('Browse Document'));
      await tester.pumpAndSettle();

      // Verify file info is shown
      expect(find.text('Pune_KVK_Soil_Report.pdf'), findsOneWidget);
      expect(find.text('439.5 KB'), findsOneWidget);
      expect(find.text('PDF Document'), findsOneWidget);
      expect(find.text('Change'), findsOneWidget);

      // Verify upload button is now enabled
      final uploadBtnFinder = find.widgetWithText(ElevatedButton, 'Upload & Extract Soil Parameters');
      final btn = tester.widget<ElevatedButton>(uploadBtnFinder);
      expect(btn.onPressed, isNotNull);

      // Tap remove button
      final removeBtnFinder = find.byTooltip('Remove selected document');
      expect(removeBtnFinder, findsOneWidget);
      await tester.tap(removeBtnFinder);
      await tester.pumpAndSettle();

      // Verify reverted to empty state
      expect(find.text('Browse Document'), findsOneWidget);
      final disabledBtn = tester.widget<ElevatedButton>(uploadBtnFinder);
      expect(disabledBtn.onPressed, isNull);
    });

    testWidgets('Selecting oversized file displays validation error banner and keeps upload disabled', (tester) async {
      final oversizedPdf = UploadDocumentFile(
        name: 'Huge_Scanning.pdf',
        bytes: utf8.encode('%PDF-1.4 oversized scan data'),
        mimeType: 'application/pdf',
        sizeBytes: 18 * 1024 * 1024,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: SoilReportUploadScreen(
            farmId: 'farm-101',
            customFilePicker: () async => oversizedPdf,
          ),
        ),
      );

      await tester.tap(find.text('Browse Document'));
      await tester.pumpAndSettle();

      expect(find.textContaining('exceeds the maximum 15 MB limit'), findsOneWidget);
      final uploadBtnFinder = find.widgetWithText(ElevatedButton, 'Upload & Extract Soil Parameters');
      final btn = tester.widget<ElevatedButton>(uploadBtnFinder);
      expect(btn.onPressed, isNull);
    });

    testWidgets('Picker cancellation preserves existing state gracefully without error', (tester) async {
      bool pickedOnce = false;
      final validPdf = UploadDocumentFile(
        name: 'Initial_Valid.pdf',
        bytes: utf8.encode('%PDF-1.4 data'),
        mimeType: 'application/pdf',
        sizeBytes: 250000,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: SoilReportUploadScreen(
            farmId: 'farm-101',
            customFilePicker: () async {
              if (!pickedOnce) {
                pickedOnce = true;
                return validPdf;
              }
              // Second pick: user cancels
              return null;
            },
          ),
        ),
      );

      // First pick: select file
      await tester.tap(find.text('Browse Document'));
      await tester.pumpAndSettle();
      expect(find.text('Initial_Valid.pdf'), findsOneWidget);

      // Second pick: tap Change, user cancels
      await tester.tap(find.text('Change'));
      await tester.pumpAndSettle();

      // State preserved: Initial_Valid.pdf is still selected
      expect(find.text('Initial_Valid.pdf'), findsOneWidget);
      expect(find.textContaining('error'), findsNothing);
    });

    testWidgets('Successful upload triggers repository upload and navigates to review', (tester) async {
      tester.view.physicalSize = const Size(1280, 1024);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      bool uploadCalled = false;
      final mockHttp = MockClient((request) async {
        if (request.url.path.endsWith('/upload')) {
          uploadCalled = true;
          return http.Response(
            jsonEncode({
              'id': 'rep-new-1',
              'farm_id': 'farm-101',
              'filename': 'GoodReport.pdf',
              'storage_path': 'reports/rep-new-1.pdf',
              'mime_type': 'application/pdf',
              'file_size_bytes': 3000,
              'upload_timestamp': '2026-03-01T00:00:00Z',
              'extraction_status': 'NEEDS_REVIEW',
              'measurements': [],
            }),
            201,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('Not found', 404);
      });

      final client = ApiClient(httpClient: mockHttp);
      final repo = SoilLabRepository(client: client, httpClient: mockHttp);
      final notifier = SoilLabNotifier(farmId: 'farm-101', repo: repo);

      final validPdf = UploadDocumentFile(
        name: 'GoodReport.pdf',
        bytes: utf8.encode('%PDF-1.4 official report data'),
        mimeType: 'application/pdf',
        sizeBytes: 3000,
      );

      final router = GoRouter(
        initialLocation: '/upload',
        routes: [
          GoRoute(
            path: '/upload',
            builder: (context, state) => SoilReportUploadScreen(
              farmId: 'farm-101',
              notifier: notifier,
              customFilePicker: () async => validPdf,
            ),
          ),
          GoRoute(
            path: RoutePaths.soilLabReportReview,
            builder: (context, state) => const Scaffold(body: Text('Review Screen Destination')),
          ),
        ],
      );

      await tester.pumpWidget(
        MaterialApp.router(
          routerConfig: router,
        ),
      );

      // Select file
      await tester.tap(find.text('Browse Document'));
      await tester.pumpAndSettle();

      // Tap Upload
      await tester.tap(find.widgetWithText(ElevatedButton, 'Upload & Extract Soil Parameters'));
      await tester.pumpAndSettle();

      expect(uploadCalled, isTrue);
      expect(find.text('Review Screen Destination'), findsOneWidget);
    });
  });
}
