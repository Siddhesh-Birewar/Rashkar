import 'package:cropnet_mobile/shared/responsive/breakpoints.dart';
import 'package:cropnet_mobile/shared/widgets/app_spacing.dart';
import 'package:cropnet_mobile/shared/widgets/centered_page_container.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('CenteredPageContainer Widget Tests', () {
    testWidgets('horizontally constrains content on desktop screens', (tester) async {
      tester.view.physicalSize = const Size(1920, 1080);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CenteredPageContainer(
              child: SizedBox(
                key: Key('inner_box'),
                height: 100,
                width: double.infinity,
              ),
            ),
          ),
        ),
      );

      final constrainedBoxFinder = find.ancestor(
        of: find.byKey(const Key('inner_box')),
        matching: find.byType(ConstrainedBox),
      );

      expect(constrainedBoxFinder, findsWidgets);
      final constrainedBox = tester.widget<ConstrainedBox>(constrainedBoxFinder.first);
      expect(constrainedBox.constraints.maxWidth, AppBreakpoints.maxContentWidthStandard);
    });

    testWidgets('readable constructor clamps width to 800px', (tester) async {
      tester.view.physicalSize = const Size(1440, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CenteredPageContainer.readable(
              child: Text('Readable Form Content', key: Key('readable_text')),
            ),
          ),
        ),
      );

      final constrainedBoxFinder = find.ancestor(
        of: find.byKey(const Key('readable_text')),
        matching: find.byType(ConstrainedBox),
      );
      final constrainedBox = tester.widget<ConstrainedBox>(constrainedBoxFinder.first);
      expect(constrainedBox.constraints.maxWidth, AppBreakpoints.maxContentWidthReadable);
    });

    testWidgets('wide constructor clamps width to 1440px', (tester) async {
      tester.view.physicalSize = const Size(2560, 1440);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CenteredPageContainer.wide(
              child: Text('Wide Dashboard Content', key: Key('wide_text')),
            ),
          ),
        ),
      );

      final constrainedBoxFinder = find.ancestor(
        of: find.byKey(const Key('wide_text')),
        matching: find.byType(ConstrainedBox),
      );
      final constrainedBox = tester.widget<ConstrainedBox>(constrainedBoxFinder.first);
      expect(constrainedBox.constraints.maxWidth, AppBreakpoints.maxContentWidthWide);
    });

    testWidgets('applies responsive padding dynamically based on screen width', (tester) async {
      // Mobile screen: padding should be md (16.0)
      tester.view.physicalSize = const Size(400, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CenteredPageContainer(
              child: Text('Padding Probe', key: Key('probe_text')),
            ),
          ),
        ),
      );

      final paddingFinder = find.ancestor(
        of: find.byKey(const Key('probe_text')),
        matching: find.byType(Padding),
      );
      final paddingWidget = tester.widget<Padding>(paddingFinder.first);
      final insets = paddingWidget.padding.resolve(TextDirection.ltr);
      expect(insets.left, AppSpacing.md);
      expect(insets.right, AppSpacing.md);
    });

    testWidgets('explicit padding overrides default responsive padding', (tester) async {
      tester.view.physicalSize = const Size(400, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      const customPadding = EdgeInsets.all(42.0);

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CenteredPageContainer(
              padding: customPadding,
              child: Text('Custom Padding Content', key: Key('custom_probe')),
            ),
          ),
        ),
      );

      final paddingFinder = find.ancestor(
        of: find.byKey(const Key('custom_probe')),
        matching: find.byType(Padding),
      );
      final paddingWidget = tester.widget<Padding>(paddingFinder.first);
      expect(paddingWidget.padding, customPadding);
    });

    testWidgets('scrollable flag wraps content in SingleChildScrollView', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CenteredPageContainer(
              scrollable: true,
              child: Text('Scrollable Content'),
            ),
          ),
        ),
      );

      expect(find.byType(SingleChildScrollView), findsOneWidget);
      expect(find.text('Scrollable Content'), findsOneWidget);
    });

    testWidgets('useSafeArea wraps content in SafeArea', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CenteredPageContainer(
              useSafeArea: true,
              child: Text('Safe Content'),
            ),
          ),
        ),
      );

      expect(find.byType(SafeArea), findsOneWidget);
      expect(find.text('Safe Content'), findsOneWidget);
    });

    testWidgets('CenteredSliverPageContainer renders in CustomScrollView', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CustomScrollView(
              slivers: [
                CenteredSliverPageContainer(
                  child: Text('Sliver Inner Content'),
                ),
              ],
            ),
          ),
        ),
      );

      expect(find.text('Sliver Inner Content'), findsOneWidget);
      expect(find.byType(SliverToBoxAdapter), findsOneWidget);
    });
  });
}
