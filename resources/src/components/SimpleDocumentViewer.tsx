import { RenderDocument } from '../types';

export function SimpleDocumentViewer({ renderDoc }: { renderDoc: RenderDocument | null }) {
  if (!renderDoc) return <div className="p-8 text-center text-gray-500 bg-gray-50 border border-gray-200 rounded-lg">No render document available</div>;
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden flex flex-col h-full">
      <div className="bg-gray-50 border-b border-gray-200 p-3 text-xs font-medium text-gray-500 uppercase tracking-wider flex justify-between">
        <span>Extracted Blocks</span>
        <span>{renderDoc.blocks.length} blocks</span>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {renderDoc.blocks.map(block => (
          <div key={block.id} className={`p-3 rounded border text-sm ${
            block.block_type === 'heading' ? 'bg-indigo-50 border-indigo-200 font-bold text-indigo-900' :
            block.block_type === 'table' ? 'bg-green-50 border-green-200 text-green-900' :
            'bg-gray-50 border-gray-200 text-gray-800'
          }`}>
            <div className="text-[10px] text-gray-400 mb-1 uppercase font-bold tracking-wider">{block.block_type}</div>
            {block.text || (block.block_type === 'table' ? '[Table Data]' : '[No Text]')}
            {block.confidence && (
              <div className="text-right mt-2 text-[10px] text-gray-400">
                Conf: {(block.confidence * 100).toFixed(1)}%
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
