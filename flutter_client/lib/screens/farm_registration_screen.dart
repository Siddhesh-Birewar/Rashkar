import 'package:flutter/material.dart';
import '../localization/app_localizations.dart';

class FarmRegistrationScreen extends StatefulWidget {
  final String lang;

  const FarmRegistrationScreen({Key? key, required this.lang}) : super(key: key);

  @override
  State<FarmRegistrationScreen> createState() => _FarmRegistrationScreenState();
}

class _FarmRegistrationScreenState extends State<FarmRegistrationScreen> {
  final _formKey = GlobalKey<FormState>();
  String _selectedTaluka = 'Baramati';
  String _selectedCrop = 'soybean';
  final _farmNameController = TextEditingController(text: 'माझे शेत १');
  final _areaController = TextEditingController(text: '3.0');
  DateTime _sowingDate = DateTime.now().subtract(const Duration(days: 45));

  final List<Map<String, String>> _talukas = [
    {'code': 'Baramati', 'name_en': 'Baramati (Canal/Rainfed)', 'name_mr': 'बारामती (बागायत/जिरायत)'},
    {'code': 'Indapur', 'name_en': 'Indapur (Semi-arid)', 'name_mr': 'इंदापूर (कोरडवाहू)'},
    {'code': 'Maval', 'name_en': 'Maval (High Rainfall)', 'name_mr': 'मावळ (जास्त पाऊस)'},
    {'code': 'Mulshi', 'name_en': 'Mulshi (Ghat Zone)', 'name_mr': 'मुळशी (घाट माथा)'},
  ];

  final List<Map<String, String>> _crops = [
    {'code': 'soybean', 'name_en': 'Soybean (सोयाबीन)'},
    {'code': 'cotton', 'name_en': 'Cotton (कापूस)'},
    {'code': 'jowar', 'name_en': 'Jowar (ज्वारी)'},
    {'code': 'sugarcane', 'name_en': 'Sugarcane (ऊस)'},
    {'code': 'gram', 'name_en': 'Gram (हरभरा)'},
    {'code': 'wheat', 'name_en': 'Wheat (गहू)'},
  ];

  @override
  Widget build(BuildContext context) {
    final lang = widget.lang;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          AppStrings.get('register_new_farm', lang: lang),
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: const Color(0xFF2E7D32),
        foregroundColor: Colors.white,
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            // Taluka Selector (Pune Pilot)
            Text(
              AppStrings.get('taluka_select', lang: lang),
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _selectedTaluka,
              decoration: InputDecoration(
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                filled: true,
                fillColor: Colors.grey.shade50,
              ),
              items: _talukas.map((t) {
                return DropdownMenuItem<String>(
                  value: t['code'],
                  child: Text(lang == 'mr' ? t['name_mr']! : t['name_en']!),
                );
              }).toList(),
              onChanged: (val) {
                if (val != null) setState(() => _selectedTaluka = val);
              },
            ),

            const SizedBox(height: 16),

            // Farm Name
            Text(
              lang == 'mr' ? 'शेताचे नाव' : 'Farm Name',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            TextFormField(
              controller: _farmNameController,
              decoration: InputDecoration(
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                hintText: 'उदा. मळ्यातील शेत',
              ),
            ),

            const SizedBox(height: 16),

            // Area in Acres
            Text(
              lang == 'mr' ? 'शेतजमीन क्षेत्र (एकर)' : 'Plot Area (Acres)',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            TextFormField(
              controller: _areaController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                suffixText: 'Acres',
              ),
            ),

            const SizedBox(height: 16),

            // Crop Selector
            Text(
              AppStrings.get('crop_select', lang: lang),
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _selectedCrop,
              decoration: InputDecoration(
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                filled: true,
                fillColor: Colors.grey.shade50,
              ),
              items: _crops.map((c) {
                return DropdownMenuItem<String>(
                  value: c['code'],
                  child: Text(c['name_en']!),
                );
              }).toList(),
              onChanged: (val) {
                if (val != null) setState(() => _selectedCrop = val);
              },
            ),

            const SizedBox(height: 16),

            // Sowing Date Picker
            Text(
              AppStrings.get('sowing_date_label', lang: lang),
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            ListTile(
              shape: RoundedRectangleBorder(
                side: BorderSide(color: Colors.grey.shade400),
                borderRadius: BorderRadius.circular(10),
              ),
              leading: const Icon(Icons.calendar_today, color: Color(0xFF2E7D32)),
              title: Text(
                '${_sowingDate.day}/${_sowingDate.month}/${_sowingDate.year}',
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              trailing: const Icon(Icons.arrow_drop_down),
              onTap: () async {
                final picked = await showDatePicker(
                  context: context,
                  initialDate: _sowingDate,
                  firstDate: DateTime(2023),
                  lastDate: DateTime.now(),
                );
                if (picked != null) {
                  setState(() => _sowingDate = picked);
                }
              },
            ),

            const SizedBox(height: 28),

            // Save Button
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF2E7D32),
                foregroundColor: Colors.white,
                minimumSize: const Size(double.infinity, 52),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      lang == 'mr'
                          ? 'शेताची माहिती यशस्वीरित्या जतन केली!'
                          : 'Farm profile saved successfully!',
                      style: const TextStyle(fontSize: 16),
                    ),
                    backgroundColor: const Color(0xFF2E7D32),
                  ),
                );
              },
              child: Text(
                AppStrings.get('save_button', lang: lang),
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
