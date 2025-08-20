import SwiftUI
import PhotosUI
import AVFoundation
import UIKit
import Speech

// MARK: - Models

struct ChatMessage: Identifiable, Equatable {
    let id = UUID()
    let role: String   // "You" or "AI"
    let text: String
}

enum ConverseMode: String, CaseIterable {
    case text = "Text"
    case voice = "Voice"
}

// MARK: - Speech Manager

final class SpeechManager: NSObject, ObservableObject {
    private let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    private let audioEngine = AVAudioEngine()
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var task: SFSpeechRecognitionTask?

    @Published var authorized = false
    @Published var isRecording = false

    func requestAuth() {
        SFSpeechRecognizer.requestAuthorization { status in
            DispatchQueue.main.async {
                self.authorized = (status == .authorized)
            }
        }
    }

    func startRecording(onFinal: @escaping (String) -> Void,
                        onPartial: ((String) -> Void)? = nil) throws {
        guard !isRecording else { return }
        isRecording = true

        // Audio session
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.record, mode: .measurement, options: [.duckOthers])
        try session.setActive(true, options: .notifyOthersOnDeactivation)

        request = SFSpeechAudioBufferRecognitionRequest()
        guard let request = request else { throw NSError(domain: "Speech", code: -1) }
        request.shouldReportPartialResults = true

        let inputNode = audioEngine.inputNode
        let format = inputNode.outputFormat(forBus: 0)
        inputNode.removeTap(onBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: format) { buffer, _ in
            self.request?.append(buffer)
        }

        audioEngine.prepare()
        try audioEngine.start()

        task = recognizer?.recognitionTask(with: request) { result, error in
            if let r = result {
                let text = r.bestTranscription.formattedString
                if r.isFinal {
                    onFinal(text)
                } else {
                    onPartial?(text)
                }
            }
            if error != nil || (result?.isFinal ?? false) {
                self.stopRecording()
            }
        }
    }

    func stopRecording() {
        guard isRecording else { return }
        isRecording = false
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        request?.endAudio()
        task?.cancel()
        task = nil
        request = nil
        try? AVAudioSession.sharedInstance().setActive(false)
    }
}

// MARK: - PreferenceKey for Scroll Tracking

private struct ScrollOffsetKey: PreferenceKey {
    static var defaultValue: CGFloat = 0
    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) {
        value = nextValue()
    }
}

// MARK: - ContentView

struct ContentView: View {
    // Image
    @State private var selectedImage: UIImage?
    @State private var showPhotoPicker = false
    @State private var showCameraPicker = false
    @State private var showSourceChooser = false

    // Chat
    @State private var userQuestion = ""
    @State private var chat: [ChatMessage] = []
    @State private var lastObjectLabel: String = ""

    // Networking
    @State private var isUploading = false
    private let backendBase = "https://context-learning-for-kids.onrender.com"

    // Voice
    @State private var mode: ConverseMode = .text
    @State private var partialTranscript: String = ""
    @StateObject private var speech = SpeechManager()

    // TTS
    private let speaker = AVSpeechSynthesizer()
    
    // ✅ Drag tracking for scroll
    @State private var isDragging = false

    // Scroll control
    @State private var isUserAtBottom: Bool = true

    var body: some View {
        VStack(spacing: 12) {
            // Mode picker
            Picker("Mode", selection: $mode) {
                ForEach(ConverseMode.allCases, id: \.self) { m in
                    Text(m.rawValue).tag(m)
                }
            }
            .pickerStyle(.segmented)

            // Image preview
            Group {
                if let img = selectedImage {
                    Image(uiImage: img)
                        .resizable()
                        .scaledToFit()
                        .frame(height: 220)
                        .cornerRadius(12)
                        .shadow(radius: 4)
                        .accessibilityLabel("Selected image")
                } else {
                    ZStack {
                        RoundedRectangle(cornerRadius: 12)
                            .fill(Color.gray.opacity(0.15))
                            .frame(height: 220)
                        Text("No image selected")
                            .foregroundColor(.secondary)
                    }
                }
            }

            // Source + Analyze
            HStack {
                Button {
                    showSourceChooser = true
                } label: {
                    HStack {
                        Image(systemName: "photo.on.rectangle")
                        Text("Select / Capture")
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .confirmationDialog("Choose Image Source",
                                    isPresented: $showSourceChooser,
                                    titleVisibility: .visible) {
                    Button("Photo Library") { showPhotoPicker = true }
                    Button("Camera") { showCameraPicker = true }
                    Button("Cancel", role: .cancel) { }
                }

                Button {
                    Task { await analyzeImageOnly() }
                } label: {
                    HStack {
                        Image(systemName: "wand.and.stars")
                        Text("Analyze")
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
                .disabled(selectedImage == nil || isUploading)
            }

            // Chat thread

            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 10) {
                        if !lastObjectLabel.isEmpty {
                            Text("Detected: \(lastObjectLabel)")
                                .font(.footnote)
                                .foregroundColor(.secondary)
                                .padding(.bottom, 4)
                        }

                        ForEach(chat) { msg in
                            VStack(alignment: .leading, spacing: 6) {
                                Text(msg.role)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                Text(msg.text)
                                    .padding(10)
                                    .background(msg.role == "You" ? Color.blue.opacity(0.1) : Color.green.opacity(0.1))
                                    .cornerRadius(10)
                            }
                            .id(msg.id)
                        }

                        if mode == .voice, speech.isRecording, !partialTranscript.isEmpty {
                            VStack(alignment: .leading, spacing: 6) {
                                Text("You (speaking)…").font(.caption).foregroundColor(.secondary)
                                Text(partialTranscript)
                                    .padding(10)
                                    .background(Color.blue.opacity(0.08))
                                    .cornerRadius(10)
                            }
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.bottom, 4)
                }
                .gesture(
                    DragGesture()
                        .onChanged { _ in isDragging = true }
                        .onEnded { _ in
                            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                                isDragging = false
                            }
                        }
                )
                .onChange(of: chat) { _, newValue in
                    guard let lastId = newValue.last?.id, !isDragging else { return }
                    withAnimation {
                        proxy.scrollTo(lastId, anchor: .bottom)
                    }
                }
            }


            // Input row
            if mode == .text {
                HStack {
                    TextField("Ask a question about the photo…", text: $userQuestion)
                        .textFieldStyle(.roundedBorder)
                    Button("Ask") {
                        Task { await askAboutImage(question: userQuestion) }
                    }
                    .disabled(selectedImage == nil ||
                              userQuestion.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ||
                              isUploading)
                }
            } else {
                HStack(spacing: 12) {
                    if !speech.authorized {
                        Button("Enable Speech") { speech.requestAuth() }
                    }
                    Button {
                        if speech.isRecording {
                            speech.stopRecording()
                            let text = partialTranscript.trimmingCharacters(in: .whitespacesAndNewlines)
                            if !text.isEmpty {
                                Task { await askAboutImage(question: text) }
                                partialTranscript = ""
                            }
                        } else {
                            partialTranscript = ""
                            do {
                                try speech.startRecording(onFinal: { final in
                                    Task { await askAboutImage(question: final) }
                                    DispatchQueue.main.async { partialTranscript = "" }
                                }, onPartial: { partial in
                                    DispatchQueue.main.async { partialTranscript = partial }
                                })
                            } catch {
                                appendAI("Mic error: \(error.localizedDescription)")
                            }
                        }
                    } label: {
                        HStack {
                            Image(systemName: speech.isRecording ? "stop.circle.fill" : "mic.circle.fill")
                            Text(speech.isRecording ? "Stop" : "Speak")
                        }
                    }
                    .disabled(selectedImage == nil || isUploading)
                }
            }

            if isUploading {
                ProgressView("Contacting AI…")
            }
        }
        .padding()
        .onAppear { speech.requestAuth() }
        // Pickers
        .sheet(isPresented: $showPhotoPicker) {
            PhotoLibraryPicker(selectedImage: $selectedImage)
        }
        .sheet(isPresented: $showCameraPicker) {
            CameraPicker(selectedImage: $selectedImage)
        }
    }

    // MARK: - Networking

    private func analyzeImageOnly() async {
        guard let image = selectedImage else { return }
        isUploading = true
        defer { isUploading = false }

        do {
            let url = URL(string: "\(backendBase)/analyze_image")!
            let (req, boundary) = multipartRequest(url: url, image: image)
            let body = multipartBody(image: image, boundary: boundary)
            let (data, _) = try await URLSession.shared.upload(for: req, from: body)

            if let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                if let error = obj["error"] as? String {
                    appendAI("Server error: \(error)")
                    return
                }
                let objectLabel = (obj["object_label"] as? String) ?? ""
                let ai = (obj["ai_response"] as? String) ?? "(No response)"
                lastObjectLabel = objectLabel
                appendAI(ai)
                speak(ai)
            } else {
                appendAI("Invalid response from server.")
            }
        } catch {
            appendAI("Network error: \(error.localizedDescription)")
        }
    }

    private func askAboutImage(question: String) async {
        guard let image = selectedImage else { return }
        let q = question.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !q.isEmpty else { return }

        appendYou(q)
        userQuestion = ""
        isUploading = true
        defer { isUploading = false }

        do {
            let url = URL(string: "\(backendBase)/chat_about_image")!
            let (req, boundary) = multipartRequest(url: url, image: image, extraFields: ["question": q])
            let body = multipartBody(image: image, boundary: boundary, extraFields: ["question": q])
            let (data, _) = try await URLSession.shared.upload(for: req, from: body)

            if let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                if let error = obj["error"] as? String {
                    appendAI("Server error: \(error)")
                    return
                }
                let objectLabel = (obj["object_label"] as? String) ?? lastObjectLabel
                let ai = (obj["ai_response"] as? String) ?? "(No response)"
                lastObjectLabel = objectLabel
                appendAI(ai)
                speak(ai)
            } else {
                appendAI("Invalid response from server.")
            }
        } catch {
            appendAI("Network error: \(error.localizedDescription)")
        }
    }

    // MARK: - Helpers

    private func appendYou(_ t: String) { chat.append(.init(role: "You", text: t)) }
    private func appendAI(_ t: String) { chat.append(.init(role: "AI", text: t)) }

    private func speak(_ text: String) {
        if speaker.isSpeaking {
            speaker.stopSpeaking(at: .immediate)
        }
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate
        speaker.speak(utterance)
    }

    // MARK: - Multipart helpers

    private func multipartRequest(url: URL,
                                  image: UIImage,
                                  extraFields: [String: String] = [:]) -> (URLRequest, String) {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        return (request, boundary)
    }

    private func multipartBody(image: UIImage,
                               boundary: String,
                               extraFields: [String: String] = [:]) -> Data {
        var body = Data()

        for (k, v) in extraFields {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(k)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(v)\r\n".data(using: .utf8)!)
        }

        let jpeg = resizedData(for: image, maxSize: 1024) ?? (image.jpegData(compressionQuality: 0.7) ?? Data())

        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"image.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(jpeg)
        body.append("\r\n".data(using: .utf8)!)
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        return body
    }

    private func resizedData(for image: UIImage, maxSize: CGFloat) -> Data? {
        let maxDim = max(image.size.width, image.size.height)
        guard maxDim > maxSize else { return image.jpegData(compressionQuality: 0.7) }
        let scale = maxSize / maxDim
        let newSize = CGSize(width: image.size.width * scale, height: image.size.height * scale)

        UIGraphicsBeginImageContextWithOptions(newSize, true, 1.0)
        image.draw(in: CGRect(origin: .zero, size: newSize))
        let resized = UIGraphicsGetImageFromCurrentImageContext()
        UIGraphicsEndImageContext()

        return resized?.jpegData(compressionQuality: 0.7)
    }
}

// MARK: - Photo Library picker
struct PhotoLibraryPicker: UIViewControllerRepresentable {
    @Binding var selectedImage: UIImage?

    func makeUIViewController(context: Context) -> PHPickerViewController {
        var config = PHPickerConfiguration(photoLibrary: .shared())
        config.filter = .images
        config.selectionLimit = 1
        let picker = PHPickerViewController(configuration: config)
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: PHPickerViewController, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    class Coordinator: NSObject, PHPickerViewControllerDelegate {
        let parent: PhotoLibraryPicker
        init(_ parent: PhotoLibraryPicker) { self.parent = parent }

        func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
            picker.dismiss(animated: true)
            guard let provider = results.first?.itemProvider,
                  provider.canLoadObject(ofClass: UIImage.self) else { return }
            provider.loadObject(ofClass: UIImage.self) { object, _ in
                DispatchQueue.main.async {
                    self.parent.selectedImage = object as? UIImage
                }
            }
        }
    }
}

// MARK: - Camera picker
struct CameraPicker: UIViewControllerRepresentable {
    @Binding var selectedImage: UIImage?

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType = .camera
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    class Coordinator: NSObject, UINavigationControllerDelegate, UIImagePickerControllerDelegate {
        let parent: CameraPicker
        init(_ parent: CameraPicker) { self.parent = parent }

        func imagePickerController(_ picker: UIImagePickerController,
                                   didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
            if let image = info[.originalImage] as? UIImage {
                parent.selectedImage = image
            }
            picker.dismiss(animated: true)
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            picker.dismiss(animated: true)
        }
    }
}
