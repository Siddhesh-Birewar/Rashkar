import 'package:cropnet_mobile/shared/widgets/responsive_grid.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ResponsiveGrid Widget Tests', () {
    testWidgets('adapts item widths to single column on mobile screens', (tester) async {
      tester.view.physicalSize = const Size(400, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ResponsiveGrid(
              spacing: 16,
              runSpacing: 16,
              children: [
                Text('Card 1', key: Key('c1')),
                Text('Card 2', key: Key('c2')),
              ],
            ),
          ),
        ),
      );

      final box1 = tester.widget<SizedBox>(
        find.ancestor(of: find.byKey(const Key('c1')), matching: find.byType(SizedBox)).first,
      );
      // In 1 column, width is full available width (400.0)
      expect(box1.width, 400.0);
    });

    testWidgets('adapts item widths to 2 columns on tablet screens', (tester) async {
      tester.view.physicalSize = const Size(800, 1000);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      const spacing = 16.0;
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ResponsiveGrid(
              spacing: spacing,
              runSpacing: spacing,
              children: [
                Text('Card 1', key: Key('c1')),
                Text('Card 2', key: Key('c2')),
              ],
            ),
          ),
        ),
      );

      final box1 = tester.widget<SizedBox>(
        find.ancestor(of: find.byKey(const Key('c1')), matching: find.byType(SizedBox)).first,
      );
      // In 2 columns on 800px width with 16px spacing: (800 - 16) / 2 = 392.0
      expect(box1.width, (800.0 - spacing) / 2);
    });

    testWidgets('ResponsiveGrid.metrics adapts item widths to 4 columns on desktop', (tester) async {
      tester.view.physicalSize = const Size(1200, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      const spacing = 16.0;
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ResponsiveGrid.metrics(
              spacing: spacing,
              children: [
                Text('Metric 1', key: Key('m1')),
                Text('Metric 2', key: Key('m2')),
                Text('Metric 3', key: Key('m3')),
                Text('Metric 4', key: Key('m4')),
              ],
            ),
          ),
        ),
      );

      final box1 = tester.widget<SizedBox>(
        find.ancestor(of: find.byKey(const Key('m1')), matching: find.byType(SizedBox)).first,
      );
      // In 4 columns on 1200px with 3 gaps of 16px: (1200 - 48) / 4 = 288.0
      expect(box1.width, (1200.0 - 3 * spacing) / 4);
    });

    testWidgets('ResponsiveGridView.builder renders grid with correct crossAxisCount', (tester) async {
      tester.view.physicalSize = const Size(800, 1000); // Tablet -> 2 columns
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ResponsiveGridView.builder(
              itemCount: 4,
              itemBuilder: (context, index) => Text('Item $index'),
            ),
          ),
        ),
      );

      final gridView = tester.widget<GridView>(find.byType(GridView));
      final delegate = gridView.gridDelegate as SliverGridDelegateWithFixedCrossAxisCount;
      expect(delegate.crossAxisCount, 2);
      expect(find.text('Item 0'), findsOneWidget);
    });

    testWidgets('ResponsiveGridRow renders 12-column span items', (tester) async {
      tester.view.physicalSize = const Size(1200, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ResponsiveGridRow(
              children: [
                ResponsiveGridCol(
                  mobile: 12,
                  desktop: 6,
                  child: Text('Col A', key: Key('col_a')),
                ),
                ResponsiveGridCol(
                  mobile: 12,
                  desktop: 6,
                  child: Text('Col B', key: Key('col_b')),
                ),
              ],
            ),
          ),
        ),
      );

      expect(find.text('Col A'), findsOneWidget);
      expect(find.text('Col B'), findsOneWidget);
    });
  });
}
