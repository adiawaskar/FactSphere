
// import { useState, useRef } from 'react';
// import { PageLayout } from '@/components/layout/PageLayout';
// import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
// import { Button } from '@/components/ui/button';
// import { Upload, Image as ImageIcon, AlertTriangle, CheckCircle, Loader2, Eye, Zap } from 'lucide-react';
// import { motion, AnimatePresence } from 'framer-motion';
// import { useInView } from 'react-intersection-observer';

// interface AnalysisResult {
//   isDeepfake: boolean;
//   confidence: number;
//   details: {
//     facialInconsistencies: number;
//     lightingAnomalies: number;
//     compressionArtifacts: number;
//     temporalConsistency: number;
//   };
//   explanation: string;
// }

// export default function DeepfakeDetection() {
//   const [selectedFile, setSelectedFile] = useState<File | null>(null);
//   const [previewUrl, setPreviewUrl] = useState<string | null>(null);
//   const [isAnalyzing, setIsAnalyzing] = useState(false);
//   const [result, setResult] = useState<AnalysisResult | null>(null);
//   const fileInputRef = useRef<HTMLInputElement>(null);
  
//   const [ref, inView] = useInView({
//     triggerOnce: true,
//     threshold: 0.1,
//   });

//   const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
//     const file = event.target.files?.[0];
//     if (file) {
//       setSelectedFile(file);
//       const url = URL.createObjectURL(file);
//       setPreviewUrl(url);
//       setResult(null);
//     }
//   };

//   const handleAnalyze = async () => {
//     if (!selectedFile) return;
    
//     setIsAnalyzing(true);
    
//     // Simulate AI analysis
//     await new Promise(resolve => setTimeout(resolve, 3000));
    
//     // Mock result
//     const mockResult: AnalysisResult = {
//       isDeepfake: Math.random() > 0.5,
//       confidence: Math.random() * 100,
//       details: {
//         facialInconsistencies: Math.random() * 100,
//         lightingAnomalies: Math.random() * 100,
//         compressionArtifacts: Math.random() * 100,
//         temporalConsistency: Math.random() * 100,
//       },
//       explanation: "Analysis completed using advanced neural networks trained on millions of images to detect subtle inconsistencies typical of AI-generated content."
//     };
    
//     setResult(mockResult);
//     setIsAnalyzing(false);
//   };

//   return (
//     <PageLayout className="py-8">
//       <motion.div
//         ref={ref}
//         initial={{ opacity: 0, y: 50 }}
//         animate={inView ? { opacity: 1, y: 0 } : {}}
//         transition={{ duration: 0.6 }}
//         className="space-y-8"
//       >
//         {/* Hero Section */}
//         <div className="text-center space-y-4">
//           <motion.div
//             initial={{ scale: 0 }}
//             animate={{ scale: 1 }}
//             transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
//             className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full"
//           >
//             <Eye className="h-5 w-5 text-primary" />
//             <span className="text-primary font-medium">AI-Powered Detection</span>
//           </motion.div>
          
//           <motion.h1 
//             className="text-4xl md:text-6xl font-bold text-gradient"
//             initial={{ opacity: 0 }}
//             animate={{ opacity: 1 }}
//             transition={{ delay: 0.3 }}
//           >
//             Deepfake Detection
//           </motion.h1>
          
//           <motion.p 
//             className="text-xl text-muted-foreground max-w-2xl mx-auto"
//             initial={{ opacity: 0 }}
//             animate={{ opacity: 1 }}
//             transition={{ delay: 0.4 }}
//           >
//             Upload any image to detect if it's AI-generated or authentic using our advanced machine learning algorithms
//           </motion.p>
//         </div>

//         <div className="grid lg:grid-cols-2 gap-8">
//           {/* Upload Section */}
//           <motion.div
//             initial={{ opacity: 0, x: -50 }}
//             animate={{ opacity: 1, x: 0 }}
//             transition={{ delay: 0.5 }}
//           >
//             <Card className="glass-card">
//               <CardHeader>
//                 <CardTitle className="flex items-center gap-2">
//                   <Upload className="h-5 w-5" />
//                   Upload Image
//                 </CardTitle>
//               </CardHeader>
//               <CardContent className="space-y-6">
//                 <div
//                   className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center cursor-pointer hover:border-primary/50 transition-colors"
//                   onClick={() => fileInputRef.current?.click()}
//                 >
//                   <input
//                     type="file"
//                     ref={fileInputRef}
//                     onChange={handleFileSelect}
//                     accept="image/*"
//                     className="hidden"
//                   />
                  
//                   <motion.div
//                     whileHover={{ scale: 1.05 }}
//                     className="space-y-4"
//                   >
//                     <div className="flex justify-center">
//                       <div className="p-4 bg-primary/10 rounded-full">
//                         <ImageIcon className="h-8 w-8 text-primary" />
//                       </div>
//                     </div>
//                     <div className="space-y-2">
//                       <p className="text-lg font-medium">Click to upload image</p>
//                       <p className="text-sm text-muted-foreground">
//                         Supports JPG, PNG, WebP (Max 10MB)
//                       </p>
//                     </div>
//                   </motion.div>
//                 </div>

//                 <AnimatePresence>
//                   {previewUrl && (
//                     <motion.div
//                       initial={{ opacity: 0, scale: 0.9 }}
//                       animate={{ opacity: 1, scale: 1 }}
//                       exit={{ opacity: 0, scale: 0.9 }}
//                       className="space-y-4"
//                     >
//                       <img
//                         src={previewUrl}
//                         alt="Preview"
//                         className="w-full h-48 object-cover rounded-lg"
//                       />
                      
//                       <Button
//                         onClick={handleAnalyze}
//                         disabled={isAnalyzing}
//                         className="w-full gradient-primary"
//                       >
//                         {isAnalyzing ? (
//                           <>
//                             <Loader2 className="mr-2 h-4 w-4 animate-spin" />
//                             Analyzing...
//                           </>
//                         ) : (
//                           <>
//                             <Zap className="mr-2 h-4 w-4" />
//                             Analyze Image
//                           </>
//                         )}
//                       </Button>
//                     </motion.div>
//                   )}
//                 </AnimatePresence>
//               </CardContent>
//             </Card>
//           </motion.div>

//           {/* Results Section */}
//           <motion.div
//             initial={{ opacity: 0, x: 50 }}
//             animate={{ opacity: 1, x: 0 }}
//             transition={{ delay: 0.6 }}
//           >
//             <Card className="glass-card h-full">
//               <CardHeader>
//                 <CardTitle className="flex items-center gap-2">
//                   <AlertTriangle className="h-5 w-5" />
//                   Analysis Results
//                 </CardTitle>
//               </CardHeader>
//               <CardContent>
//                 <AnimatePresence mode="wait">
//                   {!result && !isAnalyzing && (
//                     <motion.div
//                       initial={{ opacity: 0 }}
//                       animate={{ opacity: 1 }}
//                       exit={{ opacity: 0 }}
//                       className="flex items-center justify-center h-64 text-muted-foreground"
//                     >
//                       Upload an image to see analysis results
//                     </motion.div>
//                   )}

//                   {isAnalyzing && (
//                     <motion.div
//                       initial={{ opacity: 0 }}
//                       animate={{ opacity: 1 }}
//                       exit={{ opacity: 0 }}
//                       className="flex flex-col items-center justify-center h-64 space-y-4"
//                     >
//                       <Loader2 className="h-8 w-8 animate-spin text-primary" />
//                       <p className="text-muted-foreground">Analyzing image...</p>
//                     </motion.div>
//                   )}

//                   {result && (
//                     <motion.div
//                       initial={{ opacity: 0, y: 20 }}
//                       animate={{ opacity: 1, y: 0 }}
//                       className="space-y-6"
//                     >
//                       <div className="flex items-center gap-3">
//                         {result.isDeepfake ? (
//                           <AlertTriangle className="h-6 w-6 text-danger" />
//                         ) : (
//                           <CheckCircle className="h-6 w-6 text-verified" />
//                         )}
//                         <div>
//                           <h3 className="text-lg font-semibold">
//                             {result.isDeepfake ? 'Likely Deepfake' : 'Appears Authentic'}
//                           </h3>
//                           <p className="text-sm text-muted-foreground">
//                             Confidence: {result.confidence.toFixed(1)}%
//                           </p>
//                         </div>
//                       </div>

//                       <div className="space-y-3">
//                         <h4 className="font-medium">Detection Metrics</h4>
//                         {Object.entries(result.details).map(([key, value]) => (
//                           <div key={key} className="space-y-1">
//                             <div className="flex justify-between text-sm">
//                               <span className="capitalize">
//                                 {key.replace(/([A-Z])/g, ' $1').trim()}
//                               </span>
//                               <span>{value.toFixed(1)}%</span>
//                             </div>
//                             <div className="h-2 bg-muted rounded-full overflow-hidden">
//                               <motion.div
//                                 className="h-full bg-primary"
//                                 initial={{ width: 0 }}
//                                 animate={{ width: `${value}%` }}
//                                 transition={{ delay: 0.5, duration: 1 }}
//                               />
//                             </div>
//                           </div>
//                         ))}
//                       </div>

//                       <div className="p-4 bg-muted/50 rounded-lg">
//                         <p className="text-sm text-muted-foreground">
//                           {result.explanation}
//                         </p>
//                       </div>
//                     </motion.div>
//                   )}
//                 </AnimatePresence>
//               </CardContent>
//             </Card>
//           </motion.div>
//         </div>
//       </motion.div>
//     </PageLayout>
//   );
// }


// frontend/src/pages/DeepfakeDetection.tsx
import React, { useState, useRef } from 'react';
import { BarChart3 } from "lucide-react";
import { PageLayout } from '@/components/layout/PageLayout';
import { GoogleGenerativeAI } from "@google/generative-ai";

// --- ICONS (from components/icons/index.tsx) ---
const AlertTriangleIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
  </svg>
);

const EyeIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const UploadIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
  </svg>
);

const BeakerIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c.252 0 .504.021.753.064v5.714a2.25 2.25 0 00.659 1.591L14.41 15.35M9.75 3.104C11.625 2.366 14.025 2 16.5 2c3.314 0 6 2.686 6 6 0 2.485-1.483 4.634-3.69 5.586M9.75 12.896V18.75a2.25 2.25 0 01-2.25 2.25H5.25a2.25 2.25 0 01-2.25-2.25V18.75m9.31-6.104l-3.368-2.182m0 0a2.25 2.25 0 00-3.182 0l-3.368 2.182" />
    </svg>
);

const LightningBoltIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
  </svg>
);

const CheckCircleIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const XCircleIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);


// --- TYPES (from types.ts) ---
interface Artifact {
  description: string;
  details: string;
}

interface DetectionMetrics {
  facialInconsistencies: number;
  lightingAnomalies: number;
  compressionArtifacts: number;
  contextualConsistency: number;
  temporalConsistency: number;
}

interface AnalysisResult {
  isAuthentic: boolean;
  confidence: number;
  analysis: string;
  potentialArtifacts: Artifact[];
  detectionMetrics: DetectionMetrics;
}


// --- UTILS (from utils/imageUtils.ts) ---
const fileToBase64 = (file: File): Promise<{ base64: string, mimeType: string }> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const result = reader.result as string;
      const base64 = result.split(',')[1];
      if (!base64) {
          reject(new Error("Failed to extract base64 from file."));
          return;
      }
      resolve({ base64, mimeType: file.type });
    };
    reader.onerror = error => reject(error);
  });
};


// --- SERVICE (from services/geminiService.ts) ---
const analyzeImage = async (base64Image: string, mimeType: string, genAI: GoogleGenerativeAI): Promise<AnalysisResult> => {
  const imagePart = {
    inlineData: {
      data: base64Image,
      mimeType: mimeType,
    },
  };

  const textPart = `You are a world-class expert in digital forensics, specializing in detecting high-quality, state-of-the-art AI-generated images and deepfakes. Your task is to analyze this image with extreme skepticism.

Analyze this image for any signs of AI generation, deepfaking, or digital manipulation. Pay extremely close attention to subtle, almost imperceptible artifacts that are characteristic of even the most advanced generative models. This includes, but is not limited to:
- Micro-level inconsistencies in skin texture (e.g., unnatural smoothness, repeating patterns).
- Inconsistencies in lighting, especially in reflections in the eyes (cornea reflections) and on shiny surfaces.
- Unnatural or illogical details in the background.
- Imperfectly rendered fine details like individual hair strands, fabric textures, or jewelry.
- Subtle anatomical inconsistencies in features like ears, teeth, or hands.

Be particularly critical of images that appear to be of famous individuals, as these are common targets for high-quality deepfakes. Do not be fooled by overall coherence.

Based on your forensic analysis, determine if the image is authentic or not, and provide your results in JSON format with the following fields:
- isAuthentic (boolean): True if likely authentic/real, false if likely AI-generated
- confidence (number 0-100): Confidence score
- analysis (string): Brief explanation of reasoning
- potentialArtifacts (array): List of detected artifacts with description and details
- detectionMetrics (object): Scores (0-100) for facialInconsistencies, lightingAnomalies, compressionArtifacts, contextualConsistency, temporalConsistency`;

  try {
    const model = genAI.getGenerativeModel({
      model: "gemini-flash-latest",
    });

    const result = await model.generateContent([textPart, imagePart]);
    const response = await result.response;
    let jsonText = response.text().trim();
    
    // Remove markdown code block formatting if present
    if (jsonText.startsWith('```json')) {
      jsonText = jsonText.replace(/```json\n?/g, '').replace(/```\n?$/g, '');
    } else if (jsonText.startsWith('```')) {
      jsonText = jsonText.replace(/```\n?/g, '');
    }
    
    if (!jsonText) {
      throw new Error("The API returned an empty response. The image might be too complex or unsupported.");
    }
    
    const parsedResult = JSON.parse(jsonText);
    
    if (typeof parsedResult.isAuthentic !== 'boolean' || typeof parsedResult.confidence !== 'number' || !parsedResult.detectionMetrics) {
      throw new Error("Received malformed data from the API.");
    }

    return parsedResult as AnalysisResult;

  } catch (error) {
    console.error("Error calling Gemini API:", error);
    if (error instanceof Error) {
        throw error;
    }
    throw new Error("An unknown error occurred while communicating with the AI service.");
  }
};


// --- UI COMPONENTS ---

const Loader: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      <svg className="animate-spin h-12 w-12 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p className="text-lg text-slate-500 font-medium">Analyzing image, please wait...</p>
    </div>
  );
};

interface ImageUploaderProps {
  onFileChange: (file: File | null) => void;
  imagePreview: string | null;
  onAnalyze: () => void;
  isLoading: boolean;
}

const ImageUploader: React.FC<ImageUploaderProps> = ({ onFileChange, imagePreview, onAnalyze, isLoading }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onFileChange(file);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    const file = event.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      onFileChange(file);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
  };

  return (
    <div className="flex flex-col space-y-6 h-full">
      <div 
        className={`relative flex-grow border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center transition-all duration-300 ${imagePreview ? 'p-0' : 'p-8'} hover:border-blue-500 bg-gray-50/50 cursor-pointer`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept="image/png, image/jpeg, image/webp"
          className="hidden"
        />
        {imagePreview ? (
          <img src={imagePreview} alt="Selected preview" className="object-contain max-h-[300px] md:max-h-[400px] w-full rounded-md" />
        ) : (
          <div className="text-center text-gray-500">
             <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                <UploadIcon className="mx-auto h-8 w-8 text-gray-600" />
            </div>
            <p className="font-semibold text-blue-600">Click or drag & drop to upload</p>
            <p className="text-xs mt-1">Supports: JPG, PNG, WebP (Max 10MB)</p>
          </div>
        )}
      </div>

      <button
        onClick={onAnalyze}
        disabled={!imagePreview || isLoading}
        className="w-full flex items-center justify-center bg-gradient-to-r from-blue-600 to-green-500 hover:opacity-90 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
      >
        <LightningBoltIcon className={`h-5 w-5 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
        {isLoading ? 'Analyzing...' : 'Analyze Image'}
      </button>
    </div>
  );
};

const MetricBar: React.FC<{ label: string; value: number }> = ({ label, value }) => {
  const isHighRisk = value > 70;
  
  const barColor = isHighRisk ? 'bg-red-500' : 'bg-blue-600';
  const labelColor = isHighRisk ? 'text-red-700' : 'text-gray-700';
  const valueColor = isHighRisk ? 'text-red-600' : 'text-gray-700';

  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className={`text-sm font-medium flex items-center ${labelColor}`}>
          {isHighRisk && <AlertTriangleIcon className="h-4 w-4 mr-1.5 text-red-500 flex-shrink-0" />}
          {label}
        </span>
        <span className={`text-sm font-medium ${valueColor}`}>{value.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          className={`h-2 rounded-full animate-fill ${barColor}`}
          style={{ width: `${value}%` }}
        ></div>
      </div>
    </div>
  );
};

const ResultHeader: React.FC<{ isAuthentic: boolean, confidence: number }> = ({ isAuthentic, confidence }) => {
    const resultColor = isAuthentic ? 'text-green-600' : 'text-red-600';
    const resultIcon = isAuthentic
      ? <CheckCircleIcon className="h-10 w-10 text-green-500 flex-shrink-0" />
      : <XCircleIcon className="h-10 w-10 text-red-500 flex-shrink-0" />;

    return (
        <div className="flex items-center space-x-3 sm:space-x-4">
            {resultIcon}
            <div>
                <h3 className={`text-xl sm:text-2xl font-bold ${resultColor}`}>
                    {isAuthentic ? 'Appears Authentic' : 'Potential Deepfake / AI'}
                </h3>
                <p className="text-sm text-gray-500">Confidence: {confidence.toFixed(1)}%</p>
            </div>
        </div>
    );
};

const MetricsDisplay: React.FC<{ detectionMetrics: DetectionMetrics }> = ({ detectionMetrics }) => (
    <div className="mt-6 space-y-4">
        <MetricBar label="Facial Inconsistencies" value={detectionMetrics.facialInconsistencies} />
        <MetricBar label="Lighting Anomalies" value={detectionMetrics.lightingAnomalies} />
        <MetricBar label="Compression Artifacts" value={detectionMetrics.compressionArtifacts} />
        <MetricBar label="Contextual Consistency" value={detectionMetrics.contextualConsistency} />
        <MetricBar label="Temporal Consistency" value={detectionMetrics.temporalConsistency} />
    </div>
);

const ArtifactsDisplay: React.FC<{ artifacts: Artifact[] }> = ({ artifacts }) => (
    <div className="h-full">
        <h3 className="text-lg font-bold text-gray-800 mb-3">Detected Artifacts</h3>
        <ul className="space-y-3">
            {artifacts.map((artifact, index) => (
                <li key={index} className="border-l-4 border-blue-400 pl-4 py-1">
                    <p className="font-semibold text-sm text-gray-800">{artifact.description}</p>
                    <p className="text-gray-600 text-sm">{artifact.details}</p>
                </li>
            ))}
        </ul>
    </div>
);

const SummaryDisplay: React.FC<{ analysis: string }> = ({ analysis }) => (
    <div className="h-full">
        <h3 className="text-lg font-bold text-gray-800 mb-3">AI Summary</h3>
        <div className="bg-gray-100 p-4 rounded-lg text-sm text-gray-700 space-y-2">
            <p>{analysis}</p>
            <p className="text-xs text-gray-500">Analysis completed using advanced neural networks to detect subtle inconsistencies typical of AI-generated content.</p>
        </div>
    </div>
);

// --- MAIN APP COMPONENT ---

const DeepfakeDetection: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (file: File | null) => {
    setResult(null);
    setError(null);

    if (file) {
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
        setError('Invalid file type. Please upload a PNG, JPG, or WEBP image.');
        setSelectedFile(null);
        setImagePreview(null);
        return;
      }
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        setError('File is too large. Please upload an image under 10MB.');
        setSelectedFile(null);
        setImagePreview(null);
        return;
      }
      
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setImagePreview(url);
    } else {
      setSelectedFile(null);
      setImagePreview(null);
    }
  };

  const getFriendlyErrorMessage = (error: unknown): string => {
    if (!(error instanceof Error)) return 'An unknown error occurred.';
    
    const message = error.message.toLowerCase();
    
    // Check for missing API key
    if (!import.meta.env.VITE_GEMINI_API_KEY || import.meta.env.VITE_GEMINI_API_KEY === 'your_gemini_api_key_here') {
        return 'Gemini API key is not configured. Please create a .env.local file with VITE_GEMINI_API_KEY.';
    }
    
    if (message.includes('process is not defined') || message.includes('api key not valid') || message.includes('api_key') || message.includes('invalid_api_key')) {
        return 'The API key is invalid. Please check your VITE_GEMINI_API_KEY in .env.local file.';
    }
    if (message.includes('safety') || message.includes('blocked')) return 'The image was blocked due to content safety policies.';
    if (message.includes('rate limit') || message.includes('quota')) return 'Too many requests. Please wait a moment and try again.';
    if (message.includes('empty response')) return 'The AI model could not process this image or returned an empty response.';
    if (message.includes('json') || message.includes('parse')) return 'Error parsing AI response. The image may be too complex.';
    
    // Show the actual error in development for debugging
    console.error('Full error details:', error);
    return `Error: ${error.message}. Please check the console for details.`;
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setIsLoading(true);
    setResult(null);
    setError(null);

    try {
      // Check if API key is configured
      const apiKey = import.meta.env.VITE_GEMINI_API_KEY as string;
      if (!apiKey || apiKey === 'your_gemini_api_key_here') {
        throw new Error('Gemini API key is not configured. Please create a .env.local file in the frontend directory with VITE_GEMINI_API_KEY=your_actual_key');
      }

      const genAI = new GoogleGenerativeAI(apiKey);
      const { base64, mimeType } = await fileToBase64(selectedFile);
      const analysisResult = await analyzeImage(base64, mimeType, genAI);
      setResult(analysisResult);
    } catch (err) {
      console.error('Analysis error:', err);
      setError(getFriendlyErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <PageLayout className="py-8">
    <div className="bg-slate-50 min-h-screen flex flex-col font-sans">
      <main className="flex-grow container mx-auto px-4 py-8">
        
        <div className="text-center space-y-4 mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100/60 rounded-full">
            <EyeIcon className="h-5 w-5 text-blue-600" />
            <span className="text-blue-700 font-medium text-sm">AI-Powered Detection</span>
          </div>
          
          <h1 className="text-4xl md:text-5xl font-bold text-gradient">
            Deepfake Detection
          </h1>
          
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Upload an image to detect if it's AI-generated or authentic using our advanced machine learning algorithms.
          </p>
        </div>

        <div className="max-w-6xl mx-auto space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
                <div className="bg-white/60 backdrop-blur-md border border-gray-200/80 rounded-2xl shadow-lg p-6 flex flex-col">
                    <div className="flex items-center gap-2 mb-4">
                    <UploadIcon className="h-6 w-6 text-gray-700" />
                    <h2 className="text-xl font-bold text-gray-800">Upload Image</h2>
                    </div>
                    <ImageUploader 
                    onFileChange={handleFileChange}
                    imagePreview={imagePreview}
                    onAnalyze={handleAnalyze}
                    isLoading={isLoading}
                    />
                </div>
                <div className="bg-white/60 backdrop-blur-md border border-gray-200/80 rounded-2xl shadow-lg p-6 flex flex-col">
                    <div className="flex items-center gap-2 mb-4">
                        <BarChart3  className="h-6 w-6 text-gray-700" />
                        <h2 className="text-xl font-bold text-gray-800">Analysis Results</h2>
                    </div>
                    <div className="flex-grow flex items-center justify-center">
                        {isLoading ? (
                            <Loader />
                        ) : error ? (
                            <div className="text-center text-red-600">
                                <AlertTriangleIcon className="h-12 w-12 mx-auto mb-4" />
                                <h3 className="text-lg font-bold">Analysis Failed</h3>
                                <p className="text-sm text-slate-600 mt-1">{error}</p>
                            </div>
                        ) : result ? (
                            <div className="w-full text-left animate-fade-in">
                                <ResultHeader isAuthentic={result.isAuthentic} confidence={result.confidence} />
                                <MetricsDisplay detectionMetrics={result.detectionMetrics} />
                            </div>
                        ) : (
                            <div className="text-center text-slate-500 space-y-2">
                                <p className="font-medium">Analysis results will appear here.</p>
                                <p className="text-sm">Upload an image and click "Analyze Image" to begin.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {result && !isLoading && !error && (
                <div className="animate-fade-in grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
                    {result.potentialArtifacts && result.potentialArtifacts.length > 0 && (
                        <div className="bg-white/60 backdrop-blur-md border border-gray-200/80 rounded-2xl shadow-lg p-6">
                            <ArtifactsDisplay artifacts={result.potentialArtifacts} />
                        </div>
                    )}
                     {/* This div ensures the grid doesn't collapse if there are no artifacts */}
                    {(!result.potentialArtifacts || result.potentialArtifacts.length === 0) && (
                        <div></div>
                    )}
                    <div className="bg-white/60 backdrop-blur-md border border-gray-200/80 rounded-2xl shadow-lg p-6">
                        <SummaryDisplay analysis={result.analysis} />
                    </div>
                </div>
            )}
        </div>

      </main>
    </div>
    </PageLayout>
  );
};

export default DeepfakeDetection;