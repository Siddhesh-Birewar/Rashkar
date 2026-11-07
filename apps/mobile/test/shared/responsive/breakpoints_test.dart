import 'package:cropnet_mobile/shared/responsive/breakpoints.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('AppBreakpoints Unit Tests', () {
    test('categorizes mobile widths (< 600px) accurately', () {
      expect(AppBreakpoints.fromWidth(0), AppBreakpoint.mobile);
      expect(AppBreakpoints.fromWidth(320), AppBreakpoint.mobile);
      expect(AppBreakpoints.fromWidth(414), AppBreakpoint.mobile);
      expect(AppBreakpoints.fromWidth(599.99), AppBreakpoint.mobile);

      expect(AppBreakpoint.mobile.isMobile, isTrue);
      expect(AppBreakpoint.mobile.isTablet, isFalse);
      expect(AppBreakpoint.mobile.isDesktop, isFalse);
    });

    test('categorizes tablet widths (600px - 1024px) accurately', () {
      expect(AppBreakpoints.fromWidth(600.0), AppBreakpoint.tablet);
      expect(AppBreakpoints.fromWidth(768.0), AppBreakpoint.tablet);
      expect(AppBreakpoints.fromWidth(900.0), AppBreakpoint.tablet);
      expect(AppBreakpoints.fromWidth(1024.0), AppBreakpoint.tablet);

      expect(AppBreakpoint.tablet.isMobile, isFalse);
      expect(AppBreakpoint.tablet.isTablet, isTrue);
      expect(AppBreakpoint.tablet.isDesktop, isFalse);
    });

    test('categorizes desktop widths (> 1024px) accurately', () {
      expect(AppBreakpoints.fromWidth(1024.01), AppBreakpoint.desktop);
      expect(AppBreakpoints.fromWidth(1200.0), AppBreakpoint.desktop);
      expect(AppBreakpoints.fromWidth(1440.0), AppBreakpoint.desktop);
      expect(AppBreakpoints.fromWidth(2560.0), AppBreakpoint.desktop);

      expect(AppBreakpoint.desktop.isMobile, isFalse);
      expect(AppBreakpoint.desktop.isTablet, isFalse);
      expect(AppBreakpoint.desktop.isDesktop, isTrue);
    });

    test('responsiveValueFromWidth resolves values with cascade fallback', () {
      // Full specification
      expect(
        responsiveValueFromWidth<String>(
          width: 400,
          mobile: 'M',
          tablet: 'T',
          desktop: 'D',
        ),
        'M',
      );
      expect(
        responsiveValueFromWidth<String>(
          width: 800,
          mobile: 'M',
          tablet: 'T',
          desktop: 'D',
        ),
        'T',
      );
      expect(
        responsiveValueFromWidth<String>(
          width: 1200,
          mobile: 'M',
          tablet: 'T',
          desktop: 'D',
        ),
        'D',
      );

      // Fallbacks when tablet is null
      expect(
        responsiveValueFromWidth<String>(
          width: 800,
          mobile: 'M',
          desktop: 'D',
        ),
        'M',
      );

      // Fallback when desktop is null
      expect(
        responsiveValueFromWidth<String>(
          width: 1200,
          mobile: 'M',
          tablet: 'T',
        ),
        'T',
      );
      expect(
        responsiveValueFromWidth<String>(
          width: 1200,
          mobile: 'M',
        ),
        'M',
      );
    });

    test('BoxConstraints extension methods return correct breakpoints', () {
      const mobileConstraints = BoxConstraints(maxWidth: 480);
      expect(mobileConstraints.breakpoint, AppBreakpoint.mobile);
      expect(mobileConstraints.isMobile, isTrue);
      expect(mobileConstraints.isTablet, isFalse);
      expect(mobileConstraints.isDesktop, isFalse);
      expect(
        mobileConstraints.responsiveValue(mobile: 1, tablet: 2, desktop: 3),
        1,
      );

      const tabletConstraints = BoxConstraints(maxWidth: 768);
      expect(tabletConstraints.breakpoint, AppBreakpoint.tablet);
      expect(tabletConstraints.isMobile, isFalse);
      expect(tabletConstraints.isTablet, isTrue);
      expect(tabletConstraints.isDesktop, isFalse);
      expect(
        tabletConstraints.responsiveValue(mobile: 1, tablet: 2, desktop: 3),
        2,
      );

      const desktopConstraints = BoxConstraints(maxWidth: 1280);
      expect(desktopConstraints.breakpoint, AppBreakpoint.desktop);
      expect(desktopConstraints.isMobile, isFalse);
      expect(desktopConstraints.isTablet, isFalse);
      expect(desktopConstraints.isDesktop, isTrue);
      expect(
        desktopConstraints.responsiveValue(mobile: 1, tablet: 2, desktop: 3),
        3,
      );
    });
  });

  group('BuildContext Responsive Extension Widget Tests', () {
    testWidgets('provides correct breakpoint and dimension helpers in context', (tester) async {
      tester.view.physicalSize = const Size(800, 600);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      late AppBreakpoint recordedBreakpoint;
      late bool recordedIsMobile;
      late bool recordedIsTablet;
      late bool recordedIsDesktop;
      late double recordedWidth;
      late double recordedHeight;
      late String recordedValue;

      await tester.pumpWidget(
        MaterialApp(
          home: Builder(
            builder: (context) {
              recordedBreakpoint = context.breakpoint;
              recordedIsMobile = context.isMobile;
              recordedIsTablet = context.isTablet;
              recordedIsDesktop = context.isDesktop;
              recordedWidth = context.screenWidth;
              recordedHeight = context.screenHeight;
              recordedValue = context.responsiveValue(
                mobile: 'MobileVal',
                tablet: 'TabletVal',
                desktop: 'DesktopVal',
              );
              return const SizedBox();
            },
          ),
        ),
      );

      expect(recordedBreakpoint, AppBreakpoint.tablet);
      expect(recordedIsMobile, isFalse);
      expect(recordedIsTablet, isTrue);
      expect(recordedIsDesktop, isFalse);
      expect(recordedWidth, 800.0);
      expect(recordedHeight, 600.0);
      expect(recordedValue, 'TabletVal');
    });
  });
}
