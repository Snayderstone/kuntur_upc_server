/**
 * Base de datos simulada para almacenar casos de UPC
 * Este archivo provee funcionalidad para almacenar y recuperar casos 
 * reportados desde el sistema Kuntur Detector
 */

class UpcDatabase {
    constructor() {
        // Inicializar la base de datos desde localStorage si existe
        this.casos = this.loadFromStorage() || [];
        this.nextId = this.calculateNextId();
    }
    
    /**
     * Carga los casos almacenados en localStorage
     * @returns {Array} - Array de casos o array vacío
     */
    loadFromStorage() {
        try {
            const data = localStorage.getItem('kuntur_casos_upc');
            return data ? JSON.parse(data) : [];
        } catch (error) {
            console.error('Error al cargar datos:', error);
            return [];
        }
    }
    
    /**
     * Guarda los casos en localStorage
     */
    saveToStorage() {
        try {
            localStorage.setItem('kuntur_casos_upc', JSON.stringify(this.casos));
        } catch (error) {
            console.error('Error al guardar datos:', error);
        }
    }
    
    /**
     * Calcula el próximo ID de caso basado en los existentes
     * @returns {number} - Próximo ID numérico
     */
    calculateNextId() {
        if (this.casos.length === 0) return 1;
        
        // Encuentra el ID más alto y suma 1
        const highestId = Math.max(...this.casos.map(caso => parseInt(caso.id_caso.replace('CASO-', ''), 10)));
        return highestId + 1;
    }
    
    /**
     * Agrega un nuevo caso a la base de datos
     * @param {Object} caso - Datos del caso a agregar
     * @returns {Object} - El caso agregado con su ID
     * @throws {Error} - Si faltan campos requeridos
     */
    addCaso(caso) {
        // Validar campos obligatorios
        const requiredFields = ['id_alarma', 'nombre_agente', 'cedula_agente', 
                              'nombre_victima', 'cedula_victima', 'informe_policial'];
        
        for (const field of requiredFields) {
            if (!caso[field]) {
                throw new Error(`Campo requerido faltante: ${field}`);
            }
        }
        
        // Generar ID único con formato CASO-XXXX
        const id = `CASO-${this.nextId.toString().padStart(4, '0')}`;
        this.nextId++;
        
        // Agregar fecha de creación
        const nuevoCaso = {
            ...caso,
            id_caso: id,
            fecha_creacion: new Date().toISOString(),
            estado: 'Abierto'
        };
        
        // Agregar a la colección y guardar
        this.casos.push(nuevoCaso);
        this.saveToStorage();
        
        return nuevoCaso;
    }
    
    /**
     * Obtiene todos los casos almacenados
     * @returns {Array} - Lista de todos los casos
     */
    getAllCasos() {
        return [...this.casos];
    }
    
    /**
     * Busca un caso por su ID
     * @param {string} id - ID del caso a buscar
     * @returns {Object|null} - El caso encontrado o null
     */
    getCasoById(id) {
        return this.casos.find(caso => caso.id_caso === id) || null;
    }
    
    /**
     * Busca casos por el ID de alarma asociada
     * @param {string} idAlarma - ID de la alarma
     * @returns {Array} - Lista de casos asociados a esa alarma
     */
    getCasosByAlertId(idAlarma) {
        return this.casos.filter(caso => caso.id_alarma === idAlarma);
    }
    
    /**
     * Actualiza un caso existente
     * @param {string} id - ID del caso a actualizar
     * @param {Object} nuevosDatos - Datos actualizados
     * @returns {Object|null} - El caso actualizado o null si no existe
     */
    updateCaso(id, nuevosDatos) {
        const index = this.casos.findIndex(caso => caso.id_caso === id);
        if (index === -1) return null;
        
        // Evitar actualizar el ID o fecha de creación
        const { id_caso, fecha_creacion, ...datosActualizables } = nuevosDatos;
        
        // Actualizar solo los campos proporcionados
        this.casos[index] = {
            ...this.casos[index],
            ...datosActualizables,
            ultima_actualizacion: new Date().toISOString()
        };
        
        this.saveToStorage();
        return this.casos[index];
    }
}

// Crear una instancia global
const upcDatabase = new UpcDatabase();

// Exportar la clase y la instancia
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UpcDatabase, upcDatabase };
}
