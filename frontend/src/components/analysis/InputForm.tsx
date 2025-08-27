
import { useState } from 'react';
import { Upload, Link, Type, Image, Video, Mic, FileText, Send, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface InputFormProps {
  onAnalyze: (data: any) => void;
  isAnalyzing: boolean;
}

export const InputForm = ({ onAnalyze, isAnalyzing }: InputFormProps) => {
  const [activeTab, setActiveTab] = useState('text');
  const [textInput, setTextInput] = useState('');
  const [urlInput, setUrlInput] = useState('');
  const [files, setFiles] = useState<File[]>([]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const analysisData = {
      type: activeTab,
      content: activeTab === 'text' ? textInput : activeTab === 'url' ? urlInput : files,
      timestamp: new Date().toISOString()
    };
    onAnalyze(analysisData);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  return (
    <Card className="p-6 glass-card">
      <div className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold text-gradient">Verify Information</h2>
          <p className="text-muted-foreground">
            Submit text, URLs, images, or documents for comprehensive fact-checking
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="text" className="flex items-center gap-2">
              <Type className="h-4 w-4" />
              Text
            </TabsTrigger>
            <TabsTrigger value="url" className="flex items-center gap-2">
              <Link className="h-4 w-4" />
              URL
            </TabsTrigger>
            <TabsTrigger value="image" className="flex items-center gap-2">
              <Image className="h-4 w-4" />
              Media
            </TabsTrigger>
            <TabsTrigger value="document" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Document
            </TabsTrigger>
          </TabsList>

          <form onSubmit={handleSubmit} className="space-y-4">
            <TabsContent value="text" className="space-y-4">
              <Textarea
                placeholder="Paste the claim, news article, or statement you want to verify..."
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                className="min-h-32 resize-none"
              />
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Mic className="h-4 w-4" />
                <span>Tip: You can also paste social media posts or quotes</span>
              </div>
            </TabsContent>

            <TabsContent value="url" className="space-y-4">
              <Input
                type="url"
                placeholder="https://example.com/article-to-verify"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
              />
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Link className="h-4 w-4" />
                <span>Supports articles, social media posts, and web pages</span>
              </div>
            </TabsContent>

            <TabsContent value="image" className="space-y-4">
              <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center">
                <input
                  type="file"
                  multiple
                  accept="image/*,video/*,audio/*"
                  onChange={handleFileChange}
                  className="hidden"
                  id="media-upload"
                />
                <label htmlFor="media-upload" className="cursor-pointer">
                  <div className="space-y-4">
                    <div className="flex justify-center">
                      <div className="p-4 bg-primary/10 rounded-full">
                        <Upload className="h-8 w-8 text-primary" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-lg font-medium">Upload Media Files</p>
                      <p className="text-sm text-muted-foreground">
                        Images, videos, or audio files (Max 50MB each)
                      </p>
                    </div>
                  </div>
                </label>
              </div>
              {files.length > 0 && (
                <div className="space-y-2">
                  <p className="font-medium">Selected files:</p>
                  {files.map((file, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm">
                      <FileText className="h-4 w-4" />
                      <span>{file.name}</span>
                      <span className="text-muted-foreground">
                        ({(file.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="document" className="space-y-4">
              <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center">
                <input
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={handleFileChange}
                  className="hidden"
                  id="document-upload"
                />
                <label htmlFor="document-upload" className="cursor-pointer">
                  <div className="space-y-4">
                    <div className="flex justify-center">
                      <div className="p-4 bg-secondary/10 rounded-full">
                        <FileText className="h-8 w-8 text-secondary" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-lg font-medium">Upload Documents</p>
                      <p className="text-sm text-muted-foreground">
                        PDF, Word documents, or text files
                      </p>
                    </div>
                  </div>
                </label>
              </div>
            </TabsContent>

            <Button 
              type="submit" 
              className="w-full gradient-primary hover:opacity-90 transition-opacity"
              disabled={isAnalyzing || (!textInput && !urlInput && files.length === 0)}
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Start Verification
                </>
              )}
            </Button>
          </form>
        </Tabs>
      </div>
    </Card>
  );
};
