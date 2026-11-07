import 'dart:async';
import 'dart:js_interop';
import 'dart:typed_data';
import 'package:cross_file/cross_file.dart';
import 'package:file_picker/file_picker.dart';
import 'package:web/web.dart' as web;

final class WebSimplePlatformFile extends PlatformFile {
  @override
  final String name;
  final Uint8List _bytes;
  final int _size;

  WebSimplePlatformFile({
    required this.name,
    required Uint8List bytes,
    int? size,
  })  : _bytes = bytes,
        _size = size ?? bytes.length;

  @override
  Uri get uri => Uri.parse('blob:$name');

  @override
  XFile get xFile => XFile.fromData(_bytes, name: name);

  @override
  int? lengthSync() => _size;

  @override
  Future<int?> length() async => _size;

  @override
  Future<Uint8List> readAsBytes() async => _bytes;

  @override
  Stream<Uint8List> readAsByteStream() => Stream.value(_bytes);
}

Future<PlatformFile?> pickDocumentNative({
  required List<String> allowedExtensions,
}) async {
  final completer = Completer<PlatformFile?>();
  final input = web.document.createElement('input') as web.HTMLInputElement;
  input.type = 'file';
  input.accept = allowedExtensions.map((e) => '.$e').join(',');
  input.style.display = 'none';
  web.document.body!.appendChild(input);

  input.addEventListener('change', ((web.Event _) {
    final files = input.files;
    if (files == null || files.length == 0) {
      input.remove();
      if (!completer.isCompleted) completer.complete(null);
      return;
    }
    final file = files.item(0)!;
    final reader = web.FileReader();
    reader.addEventListener('loadend', ((web.Event _) {
      final buffer = (reader.result as JSArrayBuffer?)?.toDart;
      final bytes = buffer?.asUint8List();
      input.remove();
      if (bytes != null && !completer.isCompleted) {
        completer.complete(WebSimplePlatformFile(
          name: file.name,
          size: file.size,
          bytes: bytes,
        ));
      } else if (!completer.isCompleted) {
        completer.complete(null);
      }
    }).toJS);

    reader.addEventListener('error', ((web.Event _) {
      input.remove();
      if (!completer.isCompleted) completer.complete(null);
    }).toJS);

    reader.readAsArrayBuffer(file);
  }).toJS);

  input.addEventListener('cancel', ((web.Event _) {
    input.remove();
    if (!completer.isCompleted) completer.complete(null);
  }).toJS);

  input.click();
  return completer.future;
}
