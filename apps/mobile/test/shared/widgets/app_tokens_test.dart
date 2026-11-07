import 'package:cropnet_mobile/shared/widgets/app_decorations.dart';
import 'package:cropnet_mobile/shared/widgets/app_spacing.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('AppSpacing Tokens Tests', () {
    test('defines progressive spacing tokens', () {
      expect(AppSpacing.xxs, 2.0);
      expect(AppSpacing.xs, 4.0);
      expect(AppSpacing.sm, 8.0);
      expect(AppSpacing.md, 16.0);
      expect(AppSpacing.lg, 24.0);
      expect(AppSpacing.xl, 32.0);
      expect(AppSpacing.xxl, 48.0);
      expect(AppSpacing.xxxl, 64.0);
    });

    testWidgets('computes responsive page padding correctly', (tester) async {
      tester.view.physicalSize = const Size(1200, 800); // Desktop
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      late EdgeInsets pagePadding;

      await tester.pumpWidget(
        MaterialApp(
          home: Builder(
            builder: (context) {
              pagePadding = AppSpacing.pagePadding(context);
              return const SizedBox();
            },
          ),
        ),
      );

      expect(pagePadding.horizontal, 64.0); // 32 on each side
      expect(pagePadding.vertical, 48.0); // 24 on each side
    });
  });

  group('AppDecorations & BorderRadius Tokens Tests', () {
    test('provides consistent border radius constants', () {
      expect(AppBorderRadius.xs, 4.0);
      expect(AppBorderRadius.sm, 8.0);
      expect(AppBorderRadius.md, 12.0);
      expect(AppBorderRadius.lg, 16.0);
      expect(AppBorderRadius.xl, 24.0);
      expect(AppBorderRadius.card, AppBorderRadius.allMD);
    });

    test('card decorations produce valid BoxDecorations', () {
      final cardDec = AppDecorations.card();
      expect(cardDec.color, Colors.white);
      expect(cardDec.borderRadius, AppBorderRadius.card);
      expect(cardDec.boxShadow, isNotEmpty);

      final elevatedDec = AppDecorations.elevatedCard();
      expect(elevatedDec.boxShadow, AppShadows.card);

      final outlinedDec = AppDecorations.outlinedCard();
      expect(outlinedDec.border, isNotNull);

      final accentDec = AppDecorations.accentCard(accentColor: Colors.green);
      expect(accentDec.border, isNotNull);
    });
  });
}
