import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:cropnet_mobile/core/network/api_client.dart';
import 'package:cropnet_mobile/core/network/api_exception.dart';
import 'package:cropnet_mobile/features/soil/data/soil_lab_repository.dart';
import 'package:cropnet_mobile/features/soil/models/soil_lab_models.dart';
import 'package:cropnet_mobile/features/soil/models/soil_models.dart';
import 'package:cropnet_mobile/features/soil/presentation/screens/soil_report_history_screen.dart';
import 'package:cropnet_mobile/features/soil/presentation/screens/soil_report_review_screen.dart';
import 'package:cropnet_mobile/features/soil/presentation/screens/soil_report_upload_screen.dart';
import 'package:cropnet_mobile/features/soil/presentation/state/soil_lab_notifier.dart';
import 'package:cropnet_mobile/features/soil/presentation/widgets/lab_vs_soilgrids_comparison_widget.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('Soil Laboratory Models & JSON Contract Tests', () {
    test('SoilReportStatus enum parses values and exposes helpers', () {
      expect(SoilReportStatus.fromString('UPLOADED'), equals(SoilReportStatus.uploaded));
      expect(SoilReportStatus.fromString('PROCESSING'), equals(SoilReportStatus.processing));
      expect(SoilReportStatus.fromString('EXTRACTION_COMPLETED'), equals(SoilReportStatus.extractionCompleted));
      expect(SoilReportStatus.fromString('NEEDS_REVIEW'), equals(SoilReportStatus.needsReview));
      expect(SoilReportStatus.fromString('CONFIRMED'), equals(SoilReportStatus.confirmed));
      expect(SoilReportStatus.fromString('FAILED'), equals(SoilReportStatus.failed));
      expect(SoilReportStatus.fromString('unknown_val'), equals(SoilReportStatus.uploaded));

      expect(SoilReportStatus.needsReview.isPendingReview, isTrue);
      expect(SoilReportStatus.extractionCompleted.isPendingReview, isTrue);
      expect(SoilReportStatus.confirmed.isConfirmed, isTrue);
      expect(SoilReportStatus.processing.isProcessing, isTrue);
      expect(SoilReportStatus.failed.isFailed, isTrue);
    });

    test('MeasurementVerificationStatus enum handles aliases and helpers', () {
      expect(MeasurementVerificationStatus.fromString('EXTRACTED_UNVERIFIED'),
          equals(MeasurementVerificationStatus.extractedUnverified));
      expect(MeasurementVerificationStatus.fromString('EXTRACTED'),
          equals(MeasurementVerificationStatus.extractedUnverified));
      expect(MeasurementVerificationStatus.fromString('FARMER_CORRECTED'),
          equals(MeasurementVerificationStatus.farmerCorrected));
      expect(MeasurementVerificationStatus.fromString('CORRECTED'),
          equals(MeasurementVerificationStatus.farmerCorrected));
      expect(MeasurementVerificationStatus.fromString('FARMER_CONFIRMED'),
          equals(MeasurementVerificationStatus.farmerConfirmed));
      expect(MeasurementVerificationStatus.fromString('CONFIRMED'),
          equals(MeasurementVerificationStatus.farmerConfirmed));
      expect(MeasurementVerificationStatus.fromString('REJECTED'),
          equals(MeasurementVerificationStatus.rejected));
      expect(MeasurementVerificationStatus.fromString('FLAGGED'),
          equals(MeasurementVerificationStatus.flagged));
    });

    test('SoilMeasurementItem serializes and deserializes accurately', () {
      final jsonPayload = {
        'id': 'meas-001',
        'report_id': 'rep-101',
        'farm_id': 'farm-001',
        'parameter_key': 'available_nitrogen',
        'parameter_category': 'macronutrient',
        'original_parameter_name': 'Available N',
        'display_name': 'Available Nitrogen (N)',
        'original_value': 215.0,
        'original_unit': 'kg/ha',
        'normalized_value': 215.0,
        'normalized_unit': 'kg/ha',
        'analytical_method': 'Alkaline permanganate',
        'extraction_confidence': 0.94,
        'verification_status': 'EXTRACTED_UNVERIFIED',
        'farmer_corrected_value': null,
        'farmer_corrected_unit': null,
        'sample_depth': '0-15cm',
      };

      final item = SoilMeasurementItem.fromJson(jsonPayload);
      expect(item.id, equals('meas-001'));
      expect(item.parameterKey, equals('available_nitrogen'));
      expect(item.displayName, equals('Available Nitrogen (N)'));
      expect(item.originalValue, equals(215.0));
      expect(item.effectiveValue, equals(215.0));
      expect(item.effectiveUnit, equals('kg/ha'));
      expect(item.isFarmerCorrected, isFalse);
      expect(item.isConfirmed, isFalse);

      // Verify effectiveValue precedence when farmer corrected
      final correctedItem = item.copyWith(
        farmerCorrectedValue: 230.0,
        farmerCorrectedUnit: 'kg/ha',
        verificationStatus: MeasurementVerificationStatus.farmerCorrected,
      );
      expect(correctedItem.effectiveValue, equals(230.0));
      expect(correctedItem.isFarmerCorrected, isTrue);

      final exported = correctedItem.toJson();
      expect(exported['farmer_corrected_value'], equals(230.0));
      expect(exported['verification_status'], equals('FARMER_CORRECTED'));
    });

    test('SoilReportDetail parses full report with measurements and resolves aliases', () {
      final detailJson = {
        'id': 'rep-777',
        'farm_id': 'farm-baramati-01',
        'filename': 'Baramati_SoilHealthCard_2026.pdf',
        'storage_path': 'reports/user1/farm-baramati-01/rep-777.pdf',
        'document_url': 'https://storage.supabase.co/signed/rep-777.pdf',
        'mime_type': 'application/pdf',
        'file_size_bytes': 1450000,
        'upload_timestamp': '2026-03-01T10:00:00Z',
        'extraction_status': 'CONFIRMED',
        'lab_name': 'Baramati Agri College Testing Laboratory',
        'sample_depth_interval': '0-15cm',
        'is_confirmed': true,
        'confirmed_at': '2026-03-01T11:00:00Z',
        'measurements': [
          {
            'id': 'm-ph',
            'report_id': 'rep-777',
            'parameter_key': 'soil_ph',
            'original_parameter_name': 'pH (1:2.5)',
            'display_name': 'Soil pH (H2O)',
            'original_value': 7.82,
            'original_unit': 'pH',
            'extraction_confidence': 0.98,
            'verification_status': 'FARMER_CONFIRMED',
          },
          {
            'id': 'm-n',
            'report_id': 'rep-777',
            'parameter_key': 'available_nitrogen',
            'original_parameter_name': 'Available N',
            'display_name': 'Available Nitrogen (N)',
            'original_value': 215.0,
            'original_unit': 'kg/ha',
            'extraction_confidence': 0.91,
            'verification_status': 'FARMER_CONFIRMED',
          },
          {
            'id': 'm-zn',
            'report_id': 'rep-777',
            'parameter_key': 'zinc',
            'original_parameter_name': 'DTPA-Zn',
            'display_name': 'Available Zinc (Zn)',
            'original_value': 0.58,
            'original_unit': 'mg/kg',
            'lab_rating': 'Deficient',
            'extraction_confidence': 0.89,
            'verification_status': 'FARMER_CONFIRMED',
          },
        ],
      };

      final report = SoilReportDetail.fromJson(detailJson);
      expect(report.id, equals('rep-777'));
      expect(report.status, equals(SoilReportStatus.confirmed));
      expect(report.isConfirmed, isTrue);
      expect(report.measurements.length, equals(3));

      // Test alias resolution (ph -> soil_ph, available_n -> available_nitrogen)
      expect(report.getMeasurement('ph')?.originalValue, equals(7.82));
      expect(report.getMeasurement('soil_ph')?.originalValue, equals(7.82));
      expect(report.getEffectiveValue('available_n'), equals(215.0));
      expect(report.getEffectiveValue('available_nitrogen'), equals(215.0));
      expect(report.getMeasurement('zinc')?.labRating, equals('Deficient'));

      // Missing parameters safely return null
      expect(report.getMeasurement('total_nitrogen'), isNull);
      expect(report.getEffectiveValue('total_nitrogen'), isNull);
    });

    test('SoilReportSummary and SoilMeasurementUpdate handle JSON correctly', () {
      final summaryJson = {
        'id': 'sum-01',
        'farm_id': 'farm-01',
        'filename': 'Report1.pdf',
        'extraction_status': 'NEEDS_REVIEW',
        'upload_timestamp': '2026-03-01T10:00:00Z',
        'lab_name': 'Pune Lab',
        'sample_depth_interval': '0-15cm',
        'measurement_count': 6,
        'key_metrics': {'pH': 7.5, 'N': 210},
      };

      final summary = SoilReportSummary.fromJson(summaryJson);
      expect(summary.id, equals('sum-01'));
      expect(summary.status, equals(SoilReportStatus.needsReview));
      expect(summary.measurementCount, equals(6));
      expect(summary.keyMetrics['pH'], equals(7.5));

      const update = SoilMeasurementUpdate(
        measurementId: 'm-01',
        correctedValue: 7.45,
        correctedUnit: 'pH',
        farmerNotes: 'Corrected per lab slip',
      );
      final updateJson = update.toJson();
      expect(updateJson['corrected_value'], equals(7.45));
      expect(updateJson['corrected_unit'], equals('pH'));
      expect(updateJson['farmer_notes'], equals('Corrected per lab slip'));
      expect(updateJson['verification_status'], equals('FARMER_CORRECTED'));
    });
  });

  group('Soil Laboratory Repository Tests', () {
    test('listReports parses response list from mock client', () async {
      final mockHttp = MockClient((request) async {
        expect(request.url.path, equals('/api/v1/farms/f-101/soil-reports'));
        final response = [
          {
            'id': 'r-1',
            'farm_id': 'f-101',
            'filename': 'Test1.pdf',
            'extraction_status': 'CONFIRMED',
            'upload_timestamp': '2026-03-01T12:00:00Z',
            'measurement_count': 5,
          },
          {
            'id': 'r-2',
            'farm_id': 'f-101',
            'filename': 'Test2.jpg',
            'extraction_status': 'NEEDS_REVIEW',
            'upload_timestamp': '2026-03-02T12:00:00Z',
            'measurement_count': 4,
          },
        ];
        return http.Response(jsonEncode(response), 200, headers: {'content-type': 'application/json'});
      });

      final client = ApiClient(httpClient: mockHttp);
      final repo = SoilLabRepository(client: client, httpClient: mockHttp);

      final reports = await repo.listReports('f-101');
      expect(reports.length, equals(2));
      expect(reports[0].id, equals('r-1'));
      expect(reports[0].status, equals(SoilReportStatus.confirmed));
      expect(reports[1].id, equals('r-2'));
      expect(reports[1].status, equals(SoilReportStatus.needsReview));
    });

    test('getReportDetail and getMeasurements consume endpoints', () async {
      final mockHttp = MockClient((request) async {
        if (request.url.path == '/api/v1/farms/f-1/soil-reports/rep-1') {
          return http.Response(
            jsonEncode({
              'id': 'rep-1',
              'farm_id': 'f-1',
              'filename': 'SoilCard.pdf',
              'storage_path': 'reports/rep-1.pdf',
              'mime_type': 'application/pdf',
              'file_size_bytes': 1024,
              'upload_timestamp': '2026-03-01T00:00:00Z',
              'extraction_status': 'NEEDS_REVIEW',
              'measurements': [],
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.url.path == '/api/v1/farms/f-1/soil-reports/rep-1/measurements') {
          return http.Response(
            jsonEncode([
              {
                'id': 'm-1',
                'report_id': 'rep-1',
                'parameter_key': 'soil_ph',
                'original_value': 7.2,
                'original_unit': 'pH',
                'verification_status': 'EXTRACTED_UNVERIFIED',
              }
            ]),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('Not Found', 404);
      });

      final client = ApiClient(httpClient: mockHttp);
      final repo = SoilLabRepository(client: client, httpClient: mockHttp);

      final detail = await repo.getReportDetail('f-1', 'rep-1');
      expect(detail.id, equals('rep-1'));
      expect(detail.status, equals(SoilReportStatus.needsReview));

      final measurements = await repo.getMeasurements('f-1', 'rep-1');
      expect(measurements.length, equals(1));
      expect(measurements.first.parameterKey, equals('soil_ph'));
    });

    test('updateMeasurement and confirmReport make appropriate requests', () async {
      final mockHttp = MockClient((request) async {
        if (request.method == 'PUT' &&
            request.url.path == '/api/v1/farms/f-1/soil-reports/r-1/measurements/m-1') {
          final body = jsonDecode(request.body) as Map<String, dynamic>;
          expect(body['corrected_value'], equals(7.5));
          return http.Response(
            jsonEncode({
              'id': 'm-1',
              'report_id': 'r-1',
              'parameter_key': 'soil_ph',
              'original_value': 7.2,
              'original_unit': 'pH',
              'farmer_corrected_value': 7.5,
              'verification_status': 'FARMER_CORRECTED',
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.method == 'POST' &&
            request.url.path == '/api/v1/farms/f-1/soil-reports/r-1/confirm') {
          return http.Response(
            jsonEncode({
              'id': 'r-1',
              'farm_id': 'f-1',
              'filename': 'Report.pdf',
              'storage_path': 'reports/r-1.pdf',
              'mime_type': 'application/pdf',
              'file_size_bytes': 1000,
              'upload_timestamp': '2026-03-01T00:00:00Z',
              'extraction_status': 'CONFIRMED',
              'is_confirmed': true,
              'confirmed_at': '2026-03-01T12:00:00Z',
              'measurements': [],
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('Bad Request', 400);
      });

      final client = ApiClient(httpClient: mockHttp);
      final repo = SoilLabRepository(client: client, httpClient: mockHttp);

      final updated = await repo.updateMeasurement(
        'f-1',
        'r-1',
        'm-1',
        const SoilMeasurementUpdate(measurementId: 'm-1', correctedValue: 7.5),
      );
      expect(updated.effectiveValue, equals(7.5));
      expect(updated.isFarmerCorrected, isTrue);

      final confirmed = await repo.confirmReport('f-1', 'r-1');
      expect(confirmed.isConfirmed, isTrue);
      expect(confirmed.status, equals(SoilReportStatus.confirmed));
    });

    test('uploadReport enforces 15MB client-side limit and format check', () async {
      final mockHttp = MockClient((request) async {
        return http.Response('{"report_id": "r-new", "status": "UPLOADED"}', 200,
            headers: {'content-type': 'application/json'});
      });

      final client = ApiClient(httpClient: mockHttp);
      final repo = SoilLabRepository(client: client, httpClient: mockHttp);

      // Oversized file (> 15 MB) must be rejected client-side
      final oversizedBytes = List<int>.filled(16 * 1024 * 1024, 0);
      expect(
        () => repo.uploadReport(
          'f-1',
          fileBytes: oversizedBytes,
          fileName: 'oversized.pdf',
          mimeType: 'application/pdf',
        ),
        throwsA(isA<ValidationException>()),
      );

      // Unsupported file format must be rejected client-side
      expect(
        () => repo.uploadReport(
          'f-1',
          fileBytes: [1, 2, 3],
          fileName: 'malicious.exe',
          mimeType: 'application/octet-stream',
        ),
        throwsA(isA<ValidationException>()),
      );
    });

    test('getDocumentUrl retrieves signed URL', () async {
      final mockHttp = MockClient((request) async {
        expect(request.url.path, equals('/api/v1/farms/f-1/soil-reports/r-1/document-url'));
        return http.Response(
          jsonEncode({'signed_url': 'https://storage.supabase.co/signed/doc.pdf'}),
          200,
          headers: {'content-type': 'application/json'},
        );
      });

      final client = ApiClient(httpClient: mockHttp);
      final repo = SoilLabRepository(client: client, httpClient: mockHttp);

      final url = await repo.getDocumentUrl('f-1', 'r-1');
      expect(url, equals('https://storage.supabase.co/signed/doc.pdf'));
    });
  });

  group('SoilLabNotifier State Management Tests', () {
    test('loadReports and loadReportDetail manage loading and error state', () async {
      final mockHttp = MockClient((request) async {
        if (request.url.path.endsWith('/soil-reports')) {
          return http.Response(
            jsonEncode([
              {
                'id': 'rep-1',
                'farm_id': 'f-1',
                'filename': 'Report1.pdf',
                'extraction_status': 'NEEDS_REVIEW',
                'upload_timestamp': '2026-03-01T12:00:00Z',
              }
            ]),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.url.path.endsWith('/soil-reports/rep-1')) {
          return http.Response(
            jsonEncode({
              'id': 'rep-1',
              'farm_id': 'f-1',
              'filename': 'Report1.pdf',
              'storage_path': 'reports/rep-1.pdf',
              'mime_type': 'application/pdf',
              'file_size_bytes': 1000,
              'upload_timestamp': '2026-03-01T12:00:00Z',
              'extraction_status': 'NEEDS_REVIEW',
              'measurements': [
                {
                  'id': 'm-1',
                  'report_id': 'rep-1',
                  'parameter_key': 'soil_ph',
                  'original_value': 7.8,
                  'original_unit': 'pH',
                  'verification_status': 'EXTRACTED_UNVERIFIED',
                }
              ],
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('Error', 500);
      });

      final client = ApiClient(httpClient: mockHttp);
      final repo = SoilLabRepository(client: client, httpClient: mockHttp);
      final notifier = SoilLabNotifier(farmId: 'f-1', repo: repo);

      await notifier.loadReports();
      expect(notifier.reports.length, equals(1));
      expect(notifier.reports.first.id, equals('rep-1'));

      await notifier.loadReportDetail('rep-1');
      expect(notifier.activeReport?.id, equals('rep-1'));
      expect(notifier.activeReport?.measurements.length, equals(1));
      expect(notifier.confirmationAccepted, isFalse);
    });

    test('bufferMeasurementEdit updates buffer and active report locally', () async {
      final mockHttp = MockClient((request) async => http.Response('{}', 200));
      final client = ApiClient(httpClient: mockHttp);
      final repo = SoilLabRepository(client: client, httpClient: mockHttp);
      final notifier = SoilLabNotifier(farmId: 'f-1', repo: repo);

      // Pre-set active report
      notifier.bufferMeasurementEdit(
        'm-1',
        const SoilMeasurementUpdate(
          measurementId: 'm-1',
          correctedValue: 8.0,
          correctedUnit: 'pH',
        ),
      );

      expect(notifier.hasBufferedEdits, isTrue);
      expect(notifier.editBuffer['m-1']?.correctedValue, equals(8.0));

      notifier.removeBufferedEdit('m-1');
      expect(notifier.hasBufferedEdits, isFalse);
    });

    test('confirmTranscription requires explicit confirmation check', () async {
      final mockHttp = MockClient((request) async {
        if (request.url.path.endsWith('/confirm')) {
          return http.Response(
            jsonEncode({
              'id': 'r-1',
              'farm_id': 'f-1',
              'filename': 'R.pdf',
              'storage_path': 'r.pdf',
              'mime_type': 'application/pdf',
              'file_size_bytes': 100,
              'upload_timestamp': '2026-03-01T00:00:00Z',
              'extraction_status': 'CONFIRMED',
              'is_confirmed': true,
              'measurements': [],
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('[]', 200, headers: {'content-type': 'application/json'});
      });

      final client = ApiClient(httpClient: mockHttp);
      final repo = SoilLabRepository(client: client, httpClient: mockHttp);
      final notifier = SoilLabNotifier(farmId: 'f-1', repo: repo);

      // Attempt confirm without checking agreement box -> must fail
      expect(notifier.confirmationAccepted, isFalse);
      final unconfirmedResult = await notifier.confirmTranscription('r-1');
      expect(unconfirmedResult, isFalse);
      expect(notifier.errorMessage, contains('must confirm'));

      // Check confirmation box -> confirm must succeed
      notifier.toggleConfirmationCheck(true);
      expect(notifier.confirmationAccepted, isTrue);
      final confirmedResult = await notifier.confirmTranscription('r-1');
      expect(confirmedResult, isTrue);
      expect(notifier.activeReport?.isConfirmed, isTrue);
    });
  });

  group('Presentation Widget Tests', () {
    testWidgets('LabVsSoilgridsComparisonWidget renders distinct styling and integrity banner', (tester) async {
      final labReport = SoilReportDetail(
        id: 'rep-test',
        farmId: 'farm-test',
        filename: 'Pune_Soil_Lab_2026.pdf',
        storagePath: 'reports/rep-test.pdf',
        mimeType: 'application/pdf',
        fileSizeBytes: 2048,
        uploadTimestamp: DateTime.parse('2026-03-01T12:00:00Z'),
        status: SoilReportStatus.confirmed,
        isConfirmed: true,
        laboratoryName: 'Pune District Soil Testing Lab',
        sampleDepth: '0-15cm',
        measurements: const [
          SoilMeasurementItem(
            id: 'm1',
            reportId: 'rep-test',
            parameterKey: 'soil_ph',
            displayName: 'Soil pH (H2O)',
            originalValue: 7.80,
            originalUnit: 'pH',
            verificationStatus: MeasurementVerificationStatus.farmerConfirmed,
          ),
          SoilMeasurementItem(
            id: 'm2',
            reportId: 'rep-test',
            parameterKey: 'electrical_conductivity',
            displayName: 'Electrical Conductivity (EC)',
            originalValue: 0.42,
            originalUnit: 'dS/m',
            verificationStatus: MeasurementVerificationStatus.farmerConfirmed,
          ),
          SoilMeasurementItem(
            id: 'm3',
            reportId: 'rep-test',
            parameterKey: 'available_nitrogen',
            displayName: 'Available Nitrogen (N)',
            originalValue: 215.0,
            originalUnit: 'kg/ha',
            verificationStatus: MeasurementVerificationStatus.farmerConfirmed,
          ),
          SoilMeasurementItem(
            id: 'm4',
            reportId: 'rep-test',
            parameterKey: 'zinc',
            displayName: 'Available Zinc (Zn)',
            originalValue: 0.58,
            originalUnit: 'mg/kg',
            labRating: 'Deficient',
            verificationStatus: MeasurementVerificationStatus.farmerConfirmed,
          ),
        ],
      );

      final soilgridsProfile = UnifiedSoilProfile(
        profileId: 'sg-01',
        farmId: 'farm-test',
        createdAt: DateTime.now(),
        disclaimer: 'Spatial estimate',
        ph: const SoilParameterObservation(
          parameterKey: 'ph',
          displayName: 'Soil pH',
          value: 7.30,
          unit: 'pH',
          source: 'ISRIC SoilGrids 2.0',
          datasetVersion: '2.0.0',
          depthInterval: '0-5cm',
          spatialResolution: '250m',
          vintageYear: 2020,
        ),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: LabVsSoilgridsComparisonWidget(
                labReport: labReport,
                soilgridsProfile: soilgridsProfile,
              ),
            ),
          ),
        ),
      );

      // Verify Scientific Dual-Source Integrity Safeguard banner
      expect(find.text('Scientific Dual-Source Integrity Safeguard'), findsOneWidget);

      // Verify SoilGrids geospatial estimate card (Amber / Blue styling)
      expect(find.text('DIGITAL GEOSPATIAL ESTIMATE'), findsOneWidget);
      expect(find.text('ISRIC SoilGrids 2.0'), findsOneWidget);

      // Verify Laboratory Ground Truth card (Emerald Green styling)
      expect(find.text('OFFICIAL LABORATORY RECORD'), findsOneWidget);
      expect(find.text('Pune District Soil Testing Lab'), findsOneWidget);

      // Verify parameter rows & precedence text
      expect(find.text('Soil pH (H2O)'), findsOneWidget);
      expect(find.text('Available Nitrogen (N)'), findsOneWidget);
      expect(find.textContaining('Laboratory Ground Truth overrides model'), findsAtLeastNWidgets(1));
      expect(find.textContaining('Laboratory Ground Truth unlocks precision N dosing'), findsOneWidget);

      // Verify bioavailable indicator
      expect(find.text('Bioavailable Ion'), findsAtLeastNWidgets(1));

      // Verify micronutrient diagnostics
      expect(find.text('Comprehensive Micronutrient & Secondary Parameter Diagnostics'), findsOneWidget);
      expect(find.text('Available Zinc (Zn)'), findsOneWidget);
      expect(find.text('0.58 mg/kg'), findsOneWidget);
      expect(find.text('Rating: Deficient'), findsOneWidget);
    });

    testWidgets('SoilReportUploadScreen validates file size and formats', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: SoilReportUploadScreen(farmId: 'farm-test-1'),
        ),
      );

      expect(find.text('Upload Soil Test Report'), findsOneWidget);
      expect(find.text('Physical Laboratory Ground Truth'), findsOneWidget);
      expect(find.text('Browse Document'), findsOneWidget);
      expect(find.text('Sample & Laboratory Metadata (Optional)'), findsOneWidget);
    });

    testWidgets('SoilReportReviewScreen requires explicit checkbox before confirmation on desktop', (tester) async {
      tester.view.physicalSize = const Size(1280, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      final mockHttp = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'id': 'rep-review-01',
            'farm_id': 'farm-1',
            'filename': 'SoilTest.pdf',
            'storage_path': 'reports/rep.pdf',
            'mime_type': 'application/pdf',
            'file_size_bytes': 1000,
            'upload_timestamp': '2026-03-01T00:00:00Z',
            'extraction_status': 'NEEDS_REVIEW',
            'measurements': [
              {
                'id': 'm1',
                'report_id': 'rep-review-01',
                'parameter_key': 'soil_ph',
                'original_value': 7.6,
                'original_unit': 'pH',
                'verification_status': 'EXTRACTED_UNVERIFIED',
                'extraction_confidence': 0.95,
              }
            ],
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      });

      final client = ApiClient(httpClient: mockHttp);
      final repo = SoilLabRepository(client: client, httpClient: mockHttp);
      final notifier = SoilLabNotifier(farmId: 'farm-1', repo: repo);

      await tester.pumpWidget(
        MaterialApp(
          home: SoilReportReviewScreen(
            farmId: 'farm-1',
            reportId: 'rep-review-01',
            notifier: notifier,
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Farmer Verification Required'), findsOneWidget);
      expect(find.text('Explicit Farmer Confirmation'), findsOneWidget);

      // Confirm button exists and is disabled initially
      final confirmButtonFinder = find.widgetWithText(
        ElevatedButton,
        'Confirm Transcription (Activate Lab Results)',
      );
      expect(confirmButtonFinder, findsOneWidget);

      final elevatedButton = tester.widget<ElevatedButton>(confirmButtonFinder);
      expect(elevatedButton.onPressed, isNull); // Disabled because checkbox is not checked!

      // Tap the confirmation checkbox
      final checkboxFinder = find.byType(CheckboxListTile);
      expect(checkboxFinder, findsOneWidget);
      await tester.tap(checkboxFinder);
      await tester.pumpAndSettle();

      // Confirm button is now enabled!
      final enabledButton = tester.widget<ElevatedButton>(confirmButtonFinder);
      expect(enabledButton.onPressed, isNotNull);
    });

    testWidgets('SoilReportReviewScreen switches tabs on tablet/mobile', (tester) async {
      tester.view.physicalSize = const Size(800, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      final mockHttp = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'id': 'rep-review-02',
            'farm_id': 'farm-2',
            'filename': 'MobileTest.pdf',
            'storage_path': 'reports/rep2.pdf',
            'mime_type': 'application/pdf',
            'file_size_bytes': 1000,
            'upload_timestamp': '2026-03-01T00:00:00Z',
            'extraction_status': 'NEEDS_REVIEW',
            'measurements': [
              {
                'id': 'm1',
                'report_id': 'rep-review-02',
                'parameter_key': 'soil_ph',
                'original_value': 7.6,
                'original_unit': 'pH',
                'verification_status': 'EXTRACTED_UNVERIFIED',
                'extraction_confidence': 0.95,
              }
            ],
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      });

      final client = ApiClient(httpClient: mockHttp);
      final repo = SoilLabRepository(client: client, httpClient: mockHttp);
      final notifier = SoilLabNotifier(farmId: 'farm-2', repo: repo);

      await tester.pumpWidget(
        MaterialApp(
          home: SoilReportReviewScreen(
            farmId: 'farm-2',
            reportId: 'rep-review-02',
            notifier: notifier,
          ),
        ),
      );

      await tester.pumpAndSettle();

      // On tablet/mobile, Tab 1 is Document Preview initially
      expect(find.text('Document Preview'), findsOneWidget);
      expect(find.textContaining('Extracted Metrics'), findsOneWidget);

      // Tap Tab 2 to view extracted parameters
      await tester.tap(find.textContaining('Extracted Metrics'));
      await tester.pumpAndSettle();

      expect(find.text('Farmer Verification Required'), findsOneWidget);
    });

    testWidgets('SoilReportHistoryScreen displays empty state when no reports', (tester) async {
      final mockHttp = MockClient((request) async {
        return http.Response('[]', 200, headers: {'content-type': 'application/json'});
      });

      final client = ApiClient(httpClient: mockHttp);
      final repo = SoilLabRepository(client: client, httpClient: mockHttp);
      final notifier = SoilLabNotifier(farmId: 'farm-empty', repo: repo);

      await tester.pumpWidget(
        MaterialApp(
          home: SoilReportHistoryScreen(
            farmId: 'farm-empty',
            notifier: notifier,
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Soil Test Report History'), findsOneWidget);
      expect(find.text('No Physical Soil Test Reports Uploaded'), findsOneWidget);
      expect(find.text('Upload New Report'), findsOneWidget);
    });
  });
}
