import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'package:cropnet_mobile/core/router/farm_state.dart';
import 'package:cropnet_mobile/core/router/route_paths.dart';
import 'package:cropnet_mobile/main.dart';

/// Resolution outcome status for farm route lookup.
enum FarmResolutionStatus {
  loading,
  success,
  notFound,
  unauthorized,
  networkError,
  invalidId,
}

/// Typed result returned when resolving a farm identifier.
class FarmResolutionResult {
  final FarmResolutionStatus status;
  final FarmItem? farm;
  final String? message;

  const FarmResolutionResult.success(this.farm)
      : status = FarmResolutionStatus.success,
        message = null;

  const FarmResolutionResult.notFound([this.message = 'Farm not found or has been removed.'])
      : status = FarmResolutionStatus.notFound,
        farm = null;

  const FarmResolutionResult.unauthorized([this.message = 'You do not have permission to access this farm.'])
      : status = FarmResolutionStatus.unauthorized,
        farm = null;

  const FarmResolutionResult.networkError([this.message = 'Network error connecting to CropNet server.'])
      : status = FarmResolutionStatus.networkError,
        farm = null;

  const FarmResolutionResult.invalidId([this.message = 'Invalid farm identifier.'])
      : status = FarmResolutionStatus.invalidId,
        farm = null;
}

/// Asynchronous route resolver widget that safely resolves a [farmId] from
/// local reactive state or directly from the FastAPI backend.
///
/// Prevents blank screens, premature 404 crashes during initial bundle load,
/// and provides specialized, farmer-friendly error views for 404, 403, and network errors.
class FarmRouteResolver extends StatefulWidget {
  final String farmId;
  final String featureName;
  final Widget Function(BuildContext context, FarmItem farm) builder;

  const FarmRouteResolver({
    super.key,
    required this.farmId,
    required this.builder,
    this.featureName = 'Farm',
  });

  @override
  State<FarmRouteResolver> createState() => _FarmRouteResolverState();
}

class _FarmRouteResolverState extends State<FarmRouteResolver> {
  FarmItem? _resolvedFarm;
  FarmResolutionStatus _status = FarmResolutionStatus.loading;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _resolve();
  }

  @override
  void didUpdateWidget(covariant FarmRouteResolver oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.farmId != widget.farmId) {
      _resolve();
    }
  }

  Future<void> _resolve() async {
    final farmId = widget.farmId.trim();
    if (farmId.isEmpty) {
      setState(() {
        _status = FarmResolutionStatus.invalidId;
        _errorMessage = 'Invalid or empty farm identifier provided.';
      });
      return;
    }

    // 1. Synchronous check in in-memory repository
    final existing = FarmRepository.instance.getFarmById(farmId);
    if (existing != null) {
      setState(() {
        _resolvedFarm = existing;
        _status = FarmResolutionStatus.success;
      });
      return;
    }

    // 2. Asynchronous backend lookup
    setState(() {
      _status = FarmResolutionStatus.loading;
      _errorMessage = null;
    });

    try {
      final result = await FarmRepository.instance.resolveFarm(farmId);
      if (!mounted) return;

      setState(() {
        _status = result.status;
        _resolvedFarm = result.farm;
        _errorMessage = result.message;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _status = FarmResolutionStatus.networkError;
        _errorMessage = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    switch (_status) {
      case FarmResolutionStatus.loading:
        return Scaffold(
          appBar: AppBar(
            title: Text('${widget.featureName} — CropNet AI'),
            backgroundColor: const Color(0xFF1B5E20),
            foregroundColor: Colors.white,
          ),
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const CircularProgressIndicator(
                  valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF2E7D32)),
                ),
                const SizedBox(height: 20),
                Text(
                  'Resolving ${widget.featureName.toLowerCase()} details...',
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF1B5E20),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Farm ID: ${widget.farmId}',
                  style: const TextStyle(
                    fontSize: 12,
                    fontFamily: 'monospace',
                    color: Colors.black54,
                  ),
                ),
              ],
            ),
          ),
        );

      case FarmResolutionStatus.success:
        if (_resolvedFarm != null) {
          return widget.builder(context, _resolvedFarm!);
        }
        return _buildNotFoundView(context);

      case FarmResolutionStatus.notFound:
      case FarmResolutionStatus.invalidId:
        return _buildNotFoundView(context);

      case FarmResolutionStatus.unauthorized:
        return _buildUnauthorizedView(context);

      case FarmResolutionStatus.networkError:
        return _buildNetworkErrorView(context);
    }
  }

  Widget _buildNotFoundView(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Farm Not Found — CropNet AI'),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: const BoxDecoration(
                    color: Color(0xFFFFF3E0),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.location_off_outlined,
                    size: 64,
                    color: Color(0xFFE65100),
                  ),
                ),
                const SizedBox(height: 20),
                const Text(
                  'Farm No Longer Available',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1B5E20),
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 10),
                Text(
                  _errorMessage ??
                      'The requested farm (ID: "${widget.farmId}") could not be found or has been removed from your account.',
                  style: const TextStyle(fontSize: 14, color: Colors.black87, height: 1.4),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                Wrap(
                  spacing: 12,
                  runSpacing: 10,
                  alignment: WrapAlignment.center,
                  children: [
                    ElevatedButton.icon(
                      onPressed: () => context.go(RoutePaths.home),
                      icon: const Icon(Icons.dashboard_outlined),
                      label: const Text('Return to Dashboard'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF1B5E20),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    ),
                    OutlinedButton.icon(
                      onPressed: () => context.go(RoutePaths.soilTesting),
                      icon: const Icon(Icons.terrain_outlined),
                      label: const Text('Select Another Farm'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFF1B5E20),
                        side: const BorderSide(color: Color(0xFF1B5E20)),
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildUnauthorizedView(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Access Restricted — CropNet AI'),
        backgroundColor: const Color(0xFFB71C1C),
        foregroundColor: Colors.white,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: const BoxDecoration(
                    color: Color(0xFFFFEBEE),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.lock_outline,
                    size: 64,
                    color: Color(0xFFC62828),
                  ),
                ),
                const SizedBox(height: 20),
                const Text(
                  'Access Restricted',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFFB71C1C),
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 10),
                const Text(
                  'You do not have authorization to view or manage soil profiles for this parcel. Please verify your signed-in account credentials.',
                  style: TextStyle(fontSize: 14, color: Colors.black87, height: 1.4),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: () => context.go(RoutePaths.home),
                  icon: const Icon(Icons.arrow_back),
                  label: const Text('Return to My Farms'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1B5E20),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNetworkErrorView(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Connection Error — CropNet AI'),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: const BoxDecoration(
                    color: Color(0xFFECEFF1),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.cloud_off_outlined,
                    size: 64,
                    color: Color(0xFF455A64),
                  ),
                ),
                const SizedBox(height: 20),
                const Text(
                  'Unable to Connect to CropNet',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1B5E20),
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 10),
                Text(
                  _errorMessage ??
                      'Could not communicate with the local FastAPI backend to verify farm boundaries. Please ensure backend services are running.',
                  style: const TextStyle(fontSize: 13, color: Colors.black87, height: 1.4),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                Wrap(
                  spacing: 12,
                  runSpacing: 10,
                  alignment: WrapAlignment.center,
                  children: [
                    ElevatedButton.icon(
                      onPressed: _resolve,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Retry Connection'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF1B5E20),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    ),
                    OutlinedButton.icon(
                      onPressed: () => context.go(RoutePaths.home),
                      icon: const Icon(Icons.dashboard_outlined),
                      label: const Text('Go to Dashboard'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFF1B5E20),
                        side: const BorderSide(color: Color(0xFF1B5E20)),
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
