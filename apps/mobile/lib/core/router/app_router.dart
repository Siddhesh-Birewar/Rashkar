import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:cropnet_mobile/core/router/advisory_screen.dart';
import 'package:cropnet_mobile/core/router/app_shell.dart';
import 'package:cropnet_mobile/core/router/farm_state.dart';
import 'package:cropnet_mobile/core/router/history_screen.dart';
import 'package:cropnet_mobile/core/router/route_error_screen.dart';
import 'package:cropnet_mobile/core/router/route_names.dart';
import 'package:cropnet_mobile/core/router/route_paths.dart';
import 'package:cropnet_mobile/features/auth/auth_service.dart';
import 'package:cropnet_mobile/features/auth/auth_state.dart';
import 'package:cropnet_mobile/features/auth/presentation/login_screen.dart';
import 'package:cropnet_mobile/features/auth/presentation/register_screen.dart';
import 'package:cropnet_mobile/main.dart';

// Navigator Keys for Root and Stateful Shell Branches
final GlobalKey<NavigatorState> rootNavigatorKey =
    GlobalKey<NavigatorState>(debugLabel: 'root');

final GlobalKey<NavigatorState> _shellNavigatorHome =
    GlobalKey<NavigatorState>(debugLabel: 'shellHome');
final GlobalKey<NavigatorState> _shellNavigatorSoil =
    GlobalKey<NavigatorState>(debugLabel: 'shellSoil');
final GlobalKey<NavigatorState> _shellNavigatorCrops =
    GlobalKey<NavigatorState>(debugLabel: 'shellCrops');
final GlobalKey<NavigatorState> _shellNavigatorWeather =
    GlobalKey<NavigatorState>(debugLabel: 'shellWeather');
final GlobalKey<NavigatorState> _shellNavigatorAdvisory =
    GlobalKey<NavigatorState>(debugLabel: 'shellAdvisory');
final GlobalKey<NavigatorState> _shellNavigatorHistory =
    GlobalKey<NavigatorState>(debugLabel: 'shellHistory');

/// Creates and configures the CropNet AI GoRouter instance.
GoRouter createCropNetRouter({
  String initialLocation = RoutePaths.home,
  List<NavigatorObserver>? observers,
}) {
  return GoRouter(
    navigatorKey: rootNavigatorKey,
    initialLocation: initialLocation,
    observers: observers,
    debugLogDiagnostics: false,
    refreshListenable: AuthStateNotifier.instance,
    redirect: (context, state) {
      final auth = AuthService.instance;
      // In unconfigured development mode, don't force redirect to login
      if (!auth.isConfigured) return null;

      final authNotifier = AuthStateNotifier.instance;
      if (authNotifier.isLoading) return null;

      final isAuth = authNotifier.isAuthenticated;
      final location = state.matchedLocation;
      final isAuthRoute = location == RoutePaths.login || location == RoutePaths.register;

      if (!isAuth && !isAuthRoute) {
        return RoutePaths.login;
      }
      if (isAuth && isAuthRoute) {
        return RoutePaths.home;
      }
      return null;
    },
    errorBuilder: (context, state) => AppRouteErrorScreen(
      error: state.error,
      uri: state.uri.toString(),
    ),
    routes: [
      // Persistent Shell Route using IndexedStack to preserve branch state across tab switches
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) {
          return AppShell(navigationShell: navigationShell);
        },
        branches: [
          // Branch 0: Home / Dashboard (My Farms)
          StatefulShellBranch(
            navigatorKey: _shellNavigatorHome,
            routes: [
              GoRoute(
                path: RoutePaths.home,
                name: RouteNames.home,
                builder: (context, state) {
                  return ListenableBuilder(
                    listenable: FarmRepository.instance,
                    builder: (context, _) => MyFarmsDashboard(
                      farms: FarmRepository.instance.farms,
                      onAddFarm: (f) => FarmRepository.instance.addFarm(f),
                      onUpdateFarm: (f) => FarmRepository.instance.updateFarm(f),
                      onDeleteFarm: (id) => FarmRepository.instance.deleteFarm(id),
                    ),
                  );
                },
                routes: [
                  GoRoute(
                    path: 'farms/new',
                    name: RouteNames.farmNew,
                    parentNavigatorKey: rootNavigatorKey,
                    builder: (context, state) {
                      return AddEditFarmScreen(
                        onSave: (farm) {
                          FarmRepository.instance.addFarm(farm);
                          context.pop();
                        },
                      );
                    },
                  ),
                  GoRoute(
                    path: 'farms/:farmId',
                    name: RouteNames.farmDetail,
                    parentNavigatorKey: rootNavigatorKey,
                    builder: (context, state) {
                      final farmId = state.pathParameters['farmId'] ?? '';
                      final farm = FarmRepository.instance.getFarmById(farmId);
                      if (farm == null) {
                        return AppRouteErrorScreen(
                          uri: state.uri.toString(),
                          error: Exception('Farm with ID "$farmId" not found.'),
                        );
                      }
                      return FarmDetailScreen(
                        farm: farm,
                        onUpdate: (updated) => FarmRepository.instance.updateFarm(updated),
                        onDelete: (id) {
                          FarmRepository.instance.deleteFarm(id);
                          context.pop();
                        },
                      );
                    },
                  ),
                ],
              ),
            ],
          ),

          // Branch 1: Soil Testing & Metrics (Soil Intelligence)
          StatefulShellBranch(
            navigatorKey: _shellNavigatorSoil,
            routes: [
              GoRoute(
                path: RoutePaths.soilTesting,
                name: RouteNames.soilTesting,
                builder: (context, state) {
                  return ListenableBuilder(
                    listenable: FarmRepository.instance,
                    builder: (context, _) => SoilIntelligenceScreen(
                      farms: FarmRepository.instance.farms,
                    ),
                  );
                },
                routes: [
                  GoRoute(
                    path: ':farmId',
                    name: RouteNames.soilDetail,
                    parentNavigatorKey: rootNavigatorKey,
                    builder: (context, state) {
                      final farmId = state.pathParameters['farmId'] ?? '';
                      final farm = FarmRepository.instance.getFarmById(farmId);
                      if (farm == null) {
                        return AppRouteErrorScreen(
                          uri: state.uri.toString(),
                          error: Exception('Farm with ID "$farmId" not found for soil profiling.'),
                        );
                      }
                      return SoilIntelligenceReportScreen(farm: farm);
                    },
                  ),
                ],
              ),
            ],
          ),

          // Branch 2: Crop Recommendation & Feasibility (Agricultural Knowledge Base)
          StatefulShellBranch(
            navigatorKey: _shellNavigatorCrops,
            routes: [
              GoRoute(
                path: RoutePaths.cropRecommendation,
                name: RouteNames.cropRecommendation,
                builder: (context, state) => const CropCatalogScreen(),
                routes: [
                  GoRoute(
                    path: ':cropId',
                    name: RouteNames.cropDetail,
                    parentNavigatorKey: rootNavigatorKey,
                    builder: (context, state) {
                      final cropId = state.pathParameters['cropId'] ?? '';
                      try {
                        final crop = kCropKnowledgeBase.firstWhere((c) => c.id == cropId);
                        return CropDetailScreen(crop: crop, lang: WeatherLanguage.english);
                      } catch (_) {
                        return AppRouteErrorScreen(
                          uri: state.uri.toString(),
                          error: Exception('Crop with ID "$cropId" not found in knowledge base.'),
                        );
                      }
                    },
                  ),
                ],
              ),
            ],
          ),

          // Branch 3: Agro-meteorology (Weather & Climate Intelligence)
          StatefulShellBranch(
            navigatorKey: _shellNavigatorWeather,
            routes: [
              GoRoute(
                path: RoutePaths.weather,
                name: RouteNames.weather,
                builder: (context, state) {
                  return ListenableBuilder(
                    listenable: FarmRepository.instance,
                    builder: (context, _) => WeatherIntelligenceScreen(
                      farms: FarmRepository.instance.farms,
                    ),
                  );
                },
                routes: [
                  GoRoute(
                    path: ':farmId',
                    name: RouteNames.weatherDetail,
                    parentNavigatorKey: rootNavigatorKey,
                    builder: (context, state) {
                      final farmId = state.pathParameters['farmId'] ?? '';
                      final farm = FarmRepository.instance.getFarmById(farmId);
                      if (farm == null) {
                        return AppRouteErrorScreen(
                          uri: state.uri.toString(),
                          error: Exception('Farm with ID "$farmId" not found for weather intelligence.'),
                        );
                      }
                      return WeatherClimateReportScreen(farm: farm);
                    },
                  ),
                ],
              ),
            ],
          ),

          // Branch 4: AI Dialogue & Advisory (Qwen3:8B Agronomic Dialogue)
          StatefulShellBranch(
            navigatorKey: _shellNavigatorAdvisory,
            routes: [
              GoRoute(
                path: RoutePaths.advisory,
                name: RouteNames.advisory,
                builder: (context, state) => const AdvisoryScreen(),
              ),
            ],
          ),

          // Branch 5: Soil & Crop Assessment History
          StatefulShellBranch(
            navigatorKey: _shellNavigatorHistory,
            routes: [
              GoRoute(
                path: RoutePaths.history,
                name: RouteNames.history,
                builder: (context, state) => const AssessmentHistoryScreen(),
              ),
            ],
          ),
        ],
      ),

      // Standalone top-level routes
      GoRoute(
        path: RoutePaths.login,
        name: RouteNames.login,
        parentNavigatorKey: rootNavigatorKey,
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: RoutePaths.register,
        name: RouteNames.register,
        parentNavigatorKey: rootNavigatorKey,
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: RoutePaths.about,
        name: RouteNames.about,
        parentNavigatorKey: rootNavigatorKey,
        builder: (context, state) => const AboutCropNetScreen(),
      ),
    ],
  );
}

/// Global shared instance of the configured CropNet GoRouter
final GoRouter appRouter = createCropNetRouter();
