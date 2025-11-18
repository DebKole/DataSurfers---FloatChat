import { useEffect, useState } from 'react';
import Papa from 'papaparse';

export function useArgoDemoData() {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    Papa.parse('/argo_demo.csv', {
      header: true,
      download: true,
      dynamicTyping: true,
      complete: (results) => {
        const clean = results.data.filter(
          (r) => r.Prof_id !== undefined && r.Prof_id !== ''
        );
        setRows(clean);
      },
    });
  }, []);

  return rows; // [{ Prof_id, Level, TEMP, PRES, SAL, LAT, LON }, ...]
}